import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base, get_db
from backend.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def client_and_tokens():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        # Register organizer
        client.post("/api/auth/register", json={
            "email": "org@cloud.edu", "password": "pass12345", "full_name": "Org 1", "role": "organizer"
        })
        org_token = client.post("/api/auth/login", data={"username": "org@cloud.edu", "password": "pass12345"}).json()["access_token"]

        # Register attendee
        client.post("/api/auth/register", json={
            "email": "att@cloud.edu", "password": "pass12345", "full_name": "Att 1", "role": "attendee"
        })
        att_token = client.post("/api/auth/login", data={"username": "att@cloud.edu", "password": "pass12345"}).json()["access_token"]

        yield client, org_token, att_token

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def test_event_crud_and_permissions(client_and_tokens):
    client, org_token, att_token = client_and_tokens
    headers_org = {"Authorization": f"Bearer {org_token}"}
    headers_att = {"Authorization": f"Bearer {att_token}"}

    # Organizer creates event
    create_payload = {
        "title": "Cloud Dev Summit",
        "description": "Deep dive into serverless and realtime systems",
        "event_type": "in-person",
        "event_date": "2026-11-20",
        "start_time": "09:00",
        "end_time": "16:00",
        "venue": "Hall C",
        "maximum_capacity": 100,
        "registration_deadline": "2026-11-19 23:59:59"
    }
    res = client.post("/api/events", json=create_payload, headers=headers_org)
    assert res.status_code == 201
    event_id = res.json()["id"]

    # Attendee attempting to update event should be forbidden (403)
    res_att_update = client.put(f"/api/events/{event_id}", json={"title": "Hacked Title"}, headers=headers_att)
    assert res_att_update.status_code == 403

    # Organizer updates own event
    res_update = client.put(f"/api/events/{event_id}", json={"venue": "Main Hall"}, headers=headers_org)
    assert res_update.status_code == 200
    assert res_update.json()["venue"] == "Main Hall"

    # Anyone can fetch event list
    res_get = client.get("/api/events")
    assert res_get.status_code == 200
    assert len(res_get.json()) >= 1
