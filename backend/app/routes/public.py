import re, secrets
from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from ..extensions import db, limiter
from ..models import Applicant, TrainingProgramme, Enquiry, ApplicationStatusHistory
from ..services.notifications import notify_admin_new_registration

public_bp = Blueprint("public", __name__)


def err(message, code=400):
    return jsonify({"error": {"code": "validation_error", "message": message}}), code


def programme_json(p):
    return {
        "id": p.id,
        "name": p.name,
        "slug": p.slug,
        "category": p.category,
        "description": p.description,
        "learning_objectives": p.learning_objectives or [],
        "duration": p.duration,
        "image": p.image,
    }


@public_bp.get("/programmes")
@public_bp.get("/programmes/")
def programmes():
    rows = (
        TrainingProgramme.query.filter_by(is_active=True)
        .order_by(TrainingProgramme.id)
        .all()
    )
    return jsonify({"data": [programme_json(p) for p in rows]})


@public_bp.post("/applicants")
@limiter.limit("8 per hour")
def register_applicant():
    d = request.get_json(silent=True) or {}
    required = [
        "full_name",
        "phone_number",
        "location",
        "experience_level",
        "availability",
        "preferred_format",
        "programme_ids",
    ]
    missing = [x for x in required if not d.get(x)]
    if missing:
        return err("Missing required fields: " + ", ".join(missing))
    if d.get("consent") is not True:
        return err("Contact and privacy consent is required.")
    if d["experience_level"] not in ["Beginner", "Basic", "Intermediate", "Advanced"]:
        return err("Invalid experience level.")
    if d["availability"] not in ["Weekdays", "Weekends", "Flexible"]:
        return err("Invalid availability.")
    if d["preferred_format"] not in [
        "In-person",
        "Online theory + practical in-person",
    ]:
        return err("Invalid training format.")
    phone = re.sub(r"\s+", "", str(d["phone_number"]))
    # Avoid creating a duplicate if the same phone registers again within 24 hours.
    from datetime import datetime, timedelta

    existing = Applicant.query.filter(
        Applicant.phone_number == phone,
        Applicant.created_at >= datetime.utcnow() - timedelta(hours=24),
    ).first()
    if existing:
        return (
            jsonify(
                {
                    "data": {
                        "registration_reference": existing.registration_reference,
                        "duplicate": True,
                    },
                    "message": "A recent registration already exists for this phone number.",
                }
            ),
            200,
        )
    ids = list(dict.fromkeys(d["programme_ids"]))
    ps = TrainingProgramme.query.filter(
        TrainingProgramme.id.in_(ids), TrainingProgramme.is_active.is_(True)
    ).all()
    if len(ps) != len(ids):
        return err("One or more selected programmes are unavailable.")
    ref = "ANX-" + secrets.token_hex(4).upper()
    a = Applicant(
        registration_reference=ref,
        full_name=str(d["full_name"]).strip(),
        phone_number=phone,
        email=d.get("email") or None,
        location=str(d["location"]).strip(),
        region=d.get("region") or None,
        experience_level=d["experience_level"],
        training_objectives=d.get("training_objectives", ""),
        availability=d["availability"],
        preferred_format=d["preferred_format"],
        consent=True,
        programmes=ps,
    )
    db.session.add(a)
    db.session.flush()
    db.session.add(
        ApplicationStatusHistory(
            applicant_id=a.id, previous_status=None, new_status="New"
        )
    )
    db.session.commit()
    notify_admin_new_registration(a)
    return (
        jsonify(
            {
                "data": {"registration_reference": ref},
                "message": "Your interest registration has been received.",
            }
        ),
        201,
    )


@public_bp.post("/enquiries")
@limiter.limit("5 per hour")
def create_enquiry():
    d = request.get_json(silent=True) or {}
    if not d.get("name") or not d.get("message"):
        return err("Name and message are required.")
    e = Enquiry(
        name=d["name"].strip(),
        phone=d.get("phone"),
        email=d.get("email"),
        subject=d.get("subject"),
        message=d["message"],
    )
    db.session.add(e)
    db.session.commit()
    return (
        jsonify({"message": "Enquiry received. The AeroNex team will be in touch."}),
        201,
    )
