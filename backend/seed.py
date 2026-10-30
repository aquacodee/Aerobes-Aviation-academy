import os
from app import create_app
from app.extensions import db, bcrypt
from app.models import AdminUser, TrainingProgramme

app = create_app()
PROGRAMMES = [
    (
        "Basic Drone Training & Flight Safety",
        "basic-drone-training-flight-safety",
        "Introduction to drone systems, flight controls, flight fundamentals, pre-flight inspections, operational safety and responsible drone operation.",
        [
            "Identify major drone systems",
            "Perform pre-flight checks",
            "Apply safe operating procedures",
        ],
    ),
    (
        "Photogrammetry and 3D Modelling",
        "photogrammetry-3d-modelling",
        "Aerial image acquisition, flight planning for data capture, image processing, orthomosaic generation and 3D reconstruction.",
        [
            "Plan aerial image capture",
            "Process imagery",
            "Generate orthomosaics and 3D models",
        ],
    ),
    (
        "Drone Mapping and GIS Applications",
        "drone-mapping-gis",
        "Mapping workflows, geospatial data collection, orthomosaic maps, coordinate systems and spatial data interpretation.",
        [
            "Plan mapping missions",
            "Understand coordinate systems",
            "Interpret geospatial outputs",
        ],
    ),
    (
        "UAV Surveying Applications",
        "uav-surveying",
        "Introduction to drone-assisted surveying, aerial data acquisition, ground control concepts and surveying workflows.",
        [
            "Understand GCP concepts",
            "Acquire survey imagery",
            "Review survey workflows",
        ],
    ),
    (
        "Aerial Videography",
        "aerial-videography",
        "Camera operations, flight movements, cinematic techniques, shot planning and aerial video production.",
        [
            "Plan aerial shots",
            "Use controlled flight movements",
            "Capture video sequences",
        ],
    ),
    (
        "Aerial Photography",
        "aerial-photography",
        "Camera settings, composition, lighting, image capture and aerial photography techniques.",
        [
            "Select camera settings",
            "Apply composition principles",
            "Capture aerial photographs",
        ],
    ),
    (
        "Drone Pilot Licence Examination Preparation",
        "drone-pilot-licence-exam-preparation",
        "Preparation for relevant Ghana Civil Aviation Authority requirements and applicable pilot licensing examination. Covers aviation regulations, airspace awareness, meteorology, safety and operational knowledge.",
        [
            "Review aviation regulations",
            "Understand airspace and meteorology",
            "Prepare for applicable examination",
        ],
    ),
]
with app.app_context():
    db.create_all()
    email = os.getenv("ADMIN_EMAIL", "admin@aeronex.academy").lower()
    if not AdminUser.query.filter_by(email=email).first():
        db.session.add(
            AdminUser(
                full_name="AeroNex Administrator",
                email=email,
                password_hash=bcrypt.generate_password_hash(
                    os.getenv("ADMIN_PASSWORD", "ChangeThisImmediately!123")
                ).decode(),
                role="superadmin",
            )
        )
    for name, slug, desc, objs in PROGRAMMES:
        if not TrainingProgramme.query.filter_by(slug=slug).first():
            db.session.add(
                TrainingProgramme(
                    name=name,
                    slug=slug,
                    description=desc,
                    learning_objectives=objs,
                    duration="To be announced",
                )
            )
    db.session.commit()
    print("Seed complete. Change the initial admin password immediately.")
