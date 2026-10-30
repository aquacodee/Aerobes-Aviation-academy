import re, secrets, csv, io
from datetime import date
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, func
from ..extensions import db
from ..models import *
from ..utils.security import roles_required

admin_bp = Blueprint("admin", __name__)
STATUSES = [
    "New",
    "Contacted",
    "Interested",
    "Qualified",
    "Enrolled",
    "Not Interested",
    "Rejected",
]


def applicant_json(a):
    return {
        "id": a.id,
        "registration_reference": a.registration_reference,
        "full_name": a.full_name,
        "phone_number": a.phone_number,
        "email": a.email,
        "location": a.location,
        "region": a.region,
        "experience_level": a.experience_level,
        "training_objectives": a.training_objectives,
        "availability": a.availability,
        "preferred_format": a.preferred_format,
        "consent": a.consent,
        "application_status": a.application_status,
        "created_at": a.created_at.isoformat(),
        "programmes": [{"id": p.id, "name": p.name} for p in a.programmes],
        "notes": [
            {
                "id": n.id,
                "note": n.note,
                "created_at": n.created_at.isoformat(),
                "admin": n.admin.full_name if n.admin else "",
            }
            for n in a.notes
        ],
        "status_history": [
            {
                "previous_status": h.previous_status,
                "new_status": h.new_status,
                "created_at": h.created_at.isoformat(),
            }
            for h in a.status_history
        ],
    }


def admin_user():
    return AdminUser.query.get(int(get_jwt_identity()))


def log(action, kind=None, eid=None):
    db.session.add(
        AuditLog(
            admin_id=admin_user().id,
            action=action,
            entity_type=kind,
            entity_id=str(eid) if eid else None,
        )
    )


@admin_bp.get("/dashboard")
@roles_required("admin", "superadmin")
def dashboard():
    count = lambda q: q.count()
    total = Applicant.query.count()
    statuses = {
        s: count(Applicant.query.filter_by(application_status=s)) for s in STATUSES
    }
    monthly = (
        db.session.query(
            func.date_trunc("month", Applicant.created_at).label("month"),
            func.count(Applicant.id),
        )
        .group_by("month")
        .order_by("month")
        .all()
    )
    byprog = (
        db.session.query(
            TrainingProgramme.name, func.count(applicant_programmes.c.applicant_id)
        )
        .outerjoin(applicant_programmes)
        .group_by(TrainingProgramme.id)
        .all()
    )
    return jsonify(
        {
            "data": {
                "total_applicants": total,
                "new_registrations": statuses["New"],
                "contacted": statuses["Contacted"],
                "interested": statuses["Interested"],
                "enrolled": Student.query.count(),
                "active_cohorts": Cohort.query.filter_by(status="Active").count(),
                "completed_students": Student.query.filter_by(
                    training_status="Completed"
                ).count(),
                "conversion_rate": (
                    round((Student.query.count() / total * 100), 1) if total else 0
                ),
                "registration_trends": [
                    {"month": m.strftime("%Y-%m"), "count": n} for m, n in monthly
                ],
                "programme_popularity": [
                    {"programme": n, "count": c} for n, c in byprog
                ],
                "recent_registrations": [
                    applicant_json(a)
                    for a in Applicant.query.order_by(
                        Applicant.created_at.desc()
                    ).limit(6)
                ],
            }
        }
    )


@admin_bp.get("/applicants")
@roles_required("admin", "superadmin")
def applicants():
    q = Applicant.query
    search = request.args.get("search", "").strip()
    if search:
        q = q.filter(
            or_(
                Applicant.full_name.ilike(f"%{search}%"),
                Applicant.phone_number.ilike(f"%{search}%"),
                Applicant.registration_reference.ilike(f"%{search}%"),
            )
        )
    for key, col in [
        ("status", Applicant.application_status),
        ("experience", Applicant.experience_level),
    ]:
        if request.args.get(key):
            q = q.filter(col == request.args[key])
    if request.args.get("programme"):
        q = q.join(Applicant.programmes).filter(
            TrainingProgramme.id == int(request.args["programme"])
        )
    page = max(1, int(request.args.get("page", 1)))
    per = min(100, max(1, int(request.args.get("per_page", 20))))
    total = q.count()
    rows = (
        q.order_by(Applicant.created_at.desc())
        .offset((page - 1) * per)
        .limit(per)
        .all()
    )
    return jsonify(
        {
            "data": [applicant_json(a) for a in rows],
            "meta": {
                "page": page,
                "per_page": per,
                "total": total,
                "pages": (total + per - 1) // per,
            },
        }
    )


@admin_bp.get("/applicants/<int:aid>")
@roles_required("admin", "superadmin")
def applicant_detail(aid):
    a = db.get_or_404(Applicant, aid)
    return jsonify({"data": applicant_json(a)})


@admin_bp.patch("/applicants/<int:aid>")
@roles_required("admin", "superadmin")
def update_applicant(aid):
    a = db.get_or_404(Applicant, aid)
    d = request.get_json(silent=True) or {}
    for k in [
        "full_name",
        "phone_number",
        "email",
        "location",
        "region",
        "experience_level",
        "training_objectives",
        "availability",
        "preferred_format",
    ]:
        if k in d:
            setattr(a, k, d[k])
    db.session.commit()
    log("updated applicant", "Applicant", aid)
    db.session.commit()
    return jsonify({"data": applicant_json(a)})


@admin_bp.patch("/applicants/<int:aid>/status")
@roles_required("admin", "superadmin")
def update_status(aid):
    a = db.get_or_404(Applicant, aid)
    d = request.get_json(silent=True) or {}
    new = d.get("status")
    if new not in STATUSES:
        return jsonify({"error": {"message": "Invalid application status"}}), 400
    old = a.application_status
    a.application_status = new
    db.session.add(
        ApplicationStatusHistory(
            applicant_id=aid,
            previous_status=old,
            new_status=new,
            changed_by=admin_user().id,
        )
    )
    log("changed applicant status", "Applicant", aid)
    db.session.commit()
    return jsonify({"data": applicant_json(a)})


@admin_bp.post("/applicants/<int:aid>/notes")
@roles_required("admin", "superadmin")
def add_note(aid):
    a = db.get_or_404(Applicant, aid)
    d = request.get_json(silent=True) or {}
    if not d.get("note", "").strip():
        return jsonify({"error": {"message": "Note is required"}}), 400
    db.session.add(
        ApplicantNote(
            applicant_id=aid, admin_id=admin_user().id, note=d["note"].strip()
        )
    )
    log("added applicant note", "Applicant", aid)
    db.session.commit()
    return jsonify({"message": "Note added"}), 201


@admin_bp.post("/applicants/<int:aid>/enrol")
@roles_required("admin", "superadmin")
def enrol(aid):
    a = db.get_or_404(Applicant, aid)
    if Student.query.filter_by(applicant_id=aid).first():
        return jsonify({"error": {"message": "Applicant is already a student"}}), 409
    d = request.get_json(silent=True) or {}
    cohort = None
    if d.get("cohort_id"):
        cohort = db.get_or_404(Cohort, int(d["cohort_id"]))
        if len(cohort.students) >= cohort.maximum_capacity:
            return jsonify({"error": {"message": "Cohort has reached capacity"}}), 409
    s = Student(
        student_reference="ANX-STU-" + secrets.token_hex(3).upper(),
        applicant_id=aid,
        cohort_id=cohort.id if cohort else None,
    )
    a.application_status = "Enrolled"
    db.session.add(s)
    db.session.add(
        ApplicationStatusHistory(
            applicant_id=aid,
            previous_status="Qualified",
            new_status="Enrolled",
            changed_by=admin_user().id,
        )
    )
    log("enrolled applicant", "Student", s.student_reference)
    db.session.commit()
    return jsonify({"data": {"student_reference": s.student_reference}}), 201


@admin_bp.get("/students")
@roles_required("admin", "superadmin")
def students():
    rows = Student.query.order_by(Student.enrolment_date.desc()).all()
    return jsonify(
        {
            "data": [
                {
                    "id": s.id,
                    "student_reference": s.student_reference,
                    "full_name": s.applicant.full_name,
                    "phone": s.applicant.phone_number,
                    "programme": (
                        s.cohort.programme.name
                        if s.cohort
                        else (
                            s.applicant.programmes[0].name
                            if s.applicant.programmes
                            else "—"
                        )
                    ),
                    "cohort": s.cohort.name if s.cohort else "Unassigned",
                    "enrolment_date": s.enrolment_date.isoformat(),
                    "training_status": s.training_status,
                }
                for s in rows
            ]
        }
    )


@admin_bp.patch("/students/<int:sid>")
@roles_required("admin", "superadmin")
def update_student(sid):
    s = db.get_or_404(Student, sid)
    d = request.get_json(silent=True) or {}
    if d.get("training_status") not in [
        None,
        "Enrolled",
        "Training in Progress",
        "Completed",
        "Withdrawn",
    ]:
        return jsonify({"error": {"message": "Invalid student status"}}), 400
    if "training_status" in d:
        s.training_status = d["training_status"]
    if s.training_status == "Completed" and not s.completion_date:
        s.completion_date = date.today()
    db.session.commit()
    return jsonify({"message": "Student updated"})


@admin_bp.get("/programmes")
@roles_required("admin", "superadmin")
def admin_programmes():
    return jsonify(
        {
            "data": [
                {
                    **{"id": p.id},
                    **{
                        k: getattr(p, k)
                        for k in [
                            "name",
                            "slug",
                            "category",
                            "description",
                            "duration",
                            "is_active",
                            "learning_objectives",
                        ]
                    },
                }
                for p in TrainingProgramme.query.order_by(TrainingProgramme.id).all()
            ]
        }
    )


@admin_bp.post("/programmes")
@roles_required("admin", "superadmin")
def create_programme():
    d = request.get_json(silent=True) or {}
    slug = d.get("slug") or re.sub(r"[^a-z0-9]+", "-", d.get("name", "").lower()).strip(
        "-"
    )
    if not d.get("name") or not d.get("description"):
        return jsonify({"error": {"message": "Name and description are required"}}), 400
    p = TrainingProgramme(
        name=d["name"],
        slug=slug,
        description=d["description"],
        category=d.get("category", "Flight Operations"),
        duration=d.get("duration", "To be announced"),
        learning_objectives=d.get("learning_objectives", []),
        is_active=d.get("is_active", True),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"data": {"id": p.id, "slug": p.slug}}), 201


@admin_bp.patch("/programmes/<int:pid>")
@roles_required("admin", "superadmin")
def edit_programme(pid):
    p = db.get_or_404(TrainingProgramme, pid)
    d = request.get_json(silent=True) or {}
    for k in [
        "name",
        "description",
        "category",
        "duration",
        "learning_objectives",
        "is_active",
        "image",
    ]:
        if k in d:
            setattr(p, k, d[k])
    db.session.commit()
    return jsonify({"message": "Programme updated"})


@admin_bp.get("/cohorts")
@roles_required("admin", "superadmin")
def cohorts():
    return jsonify(
        {
            "data": [
                {
                    "id": c.id,
                    "name": c.name,
                    "cohort_code": c.cohort_code,
                    "programme": c.programme.name,
                    "programme_id": c.programme_id,
                    "start_date": c.start_date.isoformat(),
                    "end_date": c.end_date.isoformat(),
                    "location": c.location,
                    "maximum_capacity": c.maximum_capacity,
                    "enrolled": len(c.students),
                    "remaining_capacity": max(0, c.maximum_capacity - len(c.students)),
                    "status": c.status,
                }
                for c in Cohort.query.all()
            ]
        }
    )


@admin_bp.post("/cohorts")
@roles_required("admin", "superadmin")
def create_cohort():
    d = request.get_json(silent=True) or {}
    try:
        c = Cohort(
            name=d["name"],
            cohort_code=d["cohort_code"],
            programme_id=int(d["programme_id"]),
            start_date=date.fromisoformat(d["start_date"]),
            end_date=date.fromisoformat(d["end_date"]),
            location=d["location"],
            maximum_capacity=int(d.get("maximum_capacity", 12)),
            status=d.get("status", "Planned"),
        )
        if c.end_date < c.start_date:
            raise ValueError()
        db.session.add(c)
        db.session.commit()
        return jsonify({"data": {"id": c.id}}), 201
    except (KeyError, ValueError):
        return (
            jsonify({"error": {"message": "Provide valid cohort details and dates"}}),
            400,
        )


@admin_bp.get("/certificates")
@roles_required("admin", "superadmin")
def certificates():
    return jsonify(
        {
            "data": [
                {
                    "id": c.id,
                    "certificate_reference": c.certificate_reference,
                    "student": c.student.applicant.full_name,
                    "programme_name": c.programme_name,
                    "issue_date": c.issue_date.isoformat(),
                    "status": c.status,
                }
                for c in Certificate.query.order_by(Certificate.issue_date.desc()).all()
            ]
        }
    )


@admin_bp.post("/certificates")
@roles_required("admin", "superadmin")
def issue_certificate():
    d = request.get_json(silent=True) or {}
    s = db.get_or_404(Student, int(d.get("student_id", 0)))
    if s.training_status != "Completed":
        return (
            jsonify({"error": {"message": "Only completed students are eligible"}}),
            409,
        )
    if Certificate.query.filter_by(student_id=s.id, status="Issued").first():
        return (
            jsonify({"error": {"message": "An active certificate already exists"}}),
            409,
        )
    c = Certificate(
        student_id=s.id,
        certificate_reference="ANX-CERT-" + secrets.token_hex(4).upper(),
        programme_name=d.get("programme_name")
        or (s.cohort.programme.name if s.cohort else s.applicant.programmes[0].name),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"data": {"certificate_reference": c.certificate_reference}}), 201


@admin_bp.get("/reports")
@roles_required("admin", "superadmin")
def reports():
    return jsonify(
        {
            "data": {
                "applicants": Applicant.query.count(),
                "students": Student.query.count(),
                "completed": Student.query.filter_by(
                    training_status="Completed"
                ).count(),
                "programmes": [
                    {"name": p.name, "applicants": len(p.applicants)}
                    for p in TrainingProgramme.query.all()
                ],
            }
        }
    )


@admin_bp.get("/exports/applicants")
@roles_required("admin", "superadmin")
def export_applicants():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(
        [
            "Registration ID",
            "Name",
            "Phone",
            "Email",
            "Location",
            "Experience",
            "Status",
            "Programmes",
            "Registered",
        ]
    )
    for a in Applicant.query.order_by(Applicant.created_at.desc()).all():
        w.writerow(
            [
                a.registration_reference,
                a.full_name,
                a.phone_number,
                a.email,
                a.location,
                a.experience_level,
                a.application_status,
                ", ".join(p.name for p in a.programmes),
                a.created_at.isoformat(),
            ]
        )
    return Response(
        "\ufeff" + out.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=aeronex-applicants.csv"},
    )
