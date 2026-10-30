import pytest
from app import create_app
from app.extensions import db
from app.models import TrainingProgramme


@pytest.fixture
def client():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "JWT_SECRET_KEY": "test",
            "SECRET_KEY": "test",
        }
    )
    with app.app_context():
        db.create_all()
        p = TrainingProgramme(name="Basic", slug="basic", description="Basic course")
        db.session.add(p)
        db.session.commit()
        yield app.test_client()
        db.drop_all()


def test_programmes(client):
    r = client.get("/api/v1/programmes")
    assert r.status_code == 200
    assert r.json["data"][0]["name"] == "Basic"


def test_registration_requires_consent(client):
    r = client.post(
        "/api/v1/applicants",
        json={
            "full_name": "Test User",
            "phone_number": "0240000000",
            "location": "Accra",
            "experience_level": "Beginner",
            "availability": "Flexible",
            "preferred_format": "In-person",
            "programme_ids": [1],
        },
    )
    assert r.status_code == 400


def test_registration_success(client):
    payload = {
        "full_name": "Test User",
        "phone_number": "0240000000",
        "location": "Accra",
        "experience_level": "Beginner",
        "availability": "Flexible",
        "preferred_format": "In-person",
        "programme_ids": [1],
        "consent": True,
    }
    r = client.post("/api/v1/applicants", json=payload)
    assert r.status_code == 201
    assert r.json["data"]["registration_reference"].startswith("ANX-")
