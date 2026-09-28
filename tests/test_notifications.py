import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base, get_db
from backend.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def client_setup():
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
        # Register organizer & attendee (password >= 6 chars)
        reg1 = client.post("/api/auth/register", json={"email": "org2@cloud.edu", "password": "password123", "full_name": "Org", "role": "organizer"})
        assert reg1.status_code == 201
        org_token = client.post("/api/auth/login", data={"username": "org2@cloud.edu", "password": "password123"}).json()["access_token"]
        
        reg2 = client.post("/api/auth/register", json={"email": "att2@cloud.edu", "password": "password123", "full_name": "Att", "role": "attendee"})
        assert reg2.status_code == 201
        att_token = client.post("/api/auth/login", data={"username": "att2@cloud.edu", "password": "password123"}).json()["access_token"]

        yield client, org_token, att_token
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def test_announcement_fans_out_notifications(client_setup):
    client, org_token, att_token = client_setup
    h_org = {"Authorization": f"Bearer {org_token}"}
    h_att = {"Authorization": f"Bearer {att_token}"}

    # Org creates event
    ev_res = client.post("/api/events", json={
        "title": "Hackathon 2026", "event_date": "2026-12-05", "start_time": "08:00",
        "end_time": "20:00", "venue": "Lab 4", "maximum_capacity": 50, "registration_deadline": "2026-12-04 23:59:59"
    }, headers=h_org)
    assert ev_res.status_code == 201
    event_id = ev_res.json()["id"]

    # Attendee RSVPs GOING
    rsvp_res = client.post(f"/api/events/{event_id}/rsvp", json={"status": "GOING"}, headers=h_att)
    assert rsvp_res.status_code == 200

    # Organizer publishes announcement
    ann_res = client.post(f"/api/events/{event_id}/announcements", json={
        "title": "Venue Change", "message": "Moved to Innovation Hub Auditorium"
    }, headers=h_org)
    assert ann_res.status_code == 201

    # Attendee checks notifications
    notif_res = client.get("/api/notifications", headers=h_att)
    assert notif_res.status_code == 200
    notifications = notif_res.json()
    assert len(notifications) >= 1
    assert "Moved to Innovation Hub Auditorium" in notifications[0]["message"]
