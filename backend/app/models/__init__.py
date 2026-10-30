from datetime import datetime, date
from ..extensions import db

applicant_programmes = db.Table(
    "applicant_programmes",
    db.Column(
        "applicant_id",
        db.Integer,
        db.ForeignKey("applicants.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "programme_id",
        db.Integer,
        db.ForeignKey("training_programmes.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
)


class AdminUser(db.Model):
    __tablename__ = "admin_users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="admin")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class TrainingProgramme(db.Model):
    __tablename__ = "training_programmes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    category = db.Column(db.String(80), default="Flight Operations")
    description = db.Column(db.Text, nullable=False)
    learning_objectives = db.Column(db.JSON, default=list)
    duration = db.Column(db.String(80), default="To be announced")
    image = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Applicant(db.Model):
    __tablename__ = "applicants"
    id = db.Column(db.Integer, primary_key=True)
    registration_reference = db.Column(
        db.String(30), unique=True, nullable=False, index=True
    )
    full_name = db.Column(db.String(180), nullable=False)
    phone_number = db.Column(db.String(40), nullable=False, index=True)
    email = db.Column(db.String(255), index=True)
    location = db.Column(db.String(160), nullable=False)
    region = db.Column(db.String(100))
    experience_level = db.Column(db.String(30), nullable=False)
    training_objectives = db.Column(db.Text)
    availability = db.Column(db.String(30), nullable=False)
    preferred_format = db.Column(db.String(60), nullable=False)
    consent = db.Column(db.Boolean, nullable=False, default=False)
    application_status = db.Column(
        db.String(30), nullable=False, default="New", index=True
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    programmes = db.relationship(
        "TrainingProgramme", secondary=applicant_programmes, backref="applicants"
    )
    notes = db.relationship(
        "ApplicantNote",
        backref="applicant",
        cascade="all, delete-orphan",
        order_by="ApplicantNote.created_at.desc()",
    )
    status_history = db.relationship(
        "ApplicationStatusHistory",
        backref="applicant",
        cascade="all, delete-orphan",
        order_by="ApplicationStatusHistory.created_at.desc()",
    )


class Cohort(db.Model):
    __tablename__ = "cohorts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    cohort_code = db.Column(db.String(40), unique=True, nullable=False)
    programme_id = db.Column(
        db.Integer, db.ForeignKey("training_programmes.id"), nullable=False
    )
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(180), nullable=False)
    maximum_capacity = db.Column(db.Integer, nullable=False, default=12)
    status = db.Column(db.String(30), default="Planned", nullable=False)
    programme = db.relationship("TrainingProgramme")
    students = db.relationship("Student", backref="cohort")


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    student_reference = db.Column(
        db.String(30), unique=True, nullable=False, index=True
    )
    applicant_id = db.Column(
        db.Integer, db.ForeignKey("applicants.id"), unique=True, nullable=False
    )
    cohort_id = db.Column(db.Integer, db.ForeignKey("cohorts.id"))
    enrolment_date = db.Column(db.Date, default=date.today, nullable=False)
    training_status = db.Column(db.String(40), default="Enrolled", nullable=False)
    completion_date = db.Column(db.Date)
    applicant = db.relationship("Applicant")


class ApplicantNote(db.Model):
    __tablename__ = "applicant_notes"
    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(
        db.Integer, db.ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False
    )
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    admin = db.relationship("AdminUser")


class ApplicationStatusHistory(db.Model):
    __tablename__ = "application_status_history"
    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(
        db.Integer, db.ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False
    )
    previous_status = db.Column(db.String(30))
    new_status = db.Column(db.String(30), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey("admin_users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.relationship("AdminUser")


class Certificate(db.Model):
    __tablename__ = "certificates"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False, index=True
    )
    certificate_reference = db.Column(
        db.String(40), unique=True, nullable=False, index=True
    )
    issue_date = db.Column(db.Date, default=date.today)
    programme_name = db.Column(db.String(180), nullable=False)
    pdf_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default="Issued")
    student = db.relationship("Student")


class Enquiry(db.Model):
    __tablename__ = "enquiries"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(40))
    email = db.Column(db.String(255))
    subject = db.Column(db.String(180))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="New")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(80))
    entity_id = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.relationship("AdminUser")
