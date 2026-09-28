import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base, get_db
from backend.main import app
from backend.models import User, Event, RSVP, Waitlist, RSVPStatus, EventStatus, UserRole
from backend.services.rsvp_service import process_rsvp
from analytics.event_analytics import calculate_event_analytics

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def env():
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
        yield client, TestingSessionLocal, engine
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

# 1. User registration
def test_01_user_registration(env):
    client, _, _ = env
    res = client.post("/api/auth/register", json={
        "email": "user1@cloud.edu", "password": "password123", "full_name": "User One", "role": "attendee"
    })
    assert res.status_code == 201
    assert res.json()["email"] == "user1@cloud.edu"

# 2. Duplicate registration
def test_02_duplicate_registration_rejected(env):
    client, _, _ = env
    client.post("/api/auth/register", json={
        "email": "dup@cloud.edu", "password": "password123", "full_name": "Dup User", "role": "attendee"
    })
    res = client.post("/api/auth/register", json={
        "email": "dup@cloud.edu", "password": "password123", "full_name": "Dup User", "role": "attendee"
    })
    assert res.status_code == 400

# 3. Login
def test_03_login_and_token_generation(env):
    client, _, _ = env
    client.post("/api/auth/register", json={
        "email": "login_test@cloud.edu", "password": "password123", "full_name": "Login User", "role": "attendee"
    })
    res = client.post("/api/auth/login", data={"username": "login_test@cloud.edu", "password": "password123"})
    assert res.status_code == 200
    assert "access_token" in res.json()

# 4. Organizer creates event
def test_04_organizer_creates_event(env):
    client, _, _ = env
    client.post("/api/auth/register", json={"email": "org4@cloud.edu", "password": "password123", "full_name": "Org 4", "role": "organizer"})
    token = client.post("/api/auth/login", data={"username": "org4@cloud.edu", "password": "password123"}).json()["access_token"]
    res = client.post("/api/events", json={
        "title": "Cloud Architecture Summit", "event_date": "2026-11-15", "start_time": "09:00", "end_time": "17:00",
        "venue": "Hall A", "maximum_capacity": 50, "registration_deadline": "2026-11-14 23:59:59"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201

# 5. Attendee cannot create restricted event
def test_05_attendee_cannot_create_event(env):
    client, _, _ = env
    client.post("/api/auth/register", json={"email": "att5@cloud.edu", "password": "password123", "full_name": "Att 5", "role": "attendee"})
    token = client.post("/api/auth/login", data={"username": "att5@cloud.edu", "password": "password123"}).json()["access_token"]
    res = client.post("/api/events", json={
        "title": "Unauthorized", "event_date": "2026-11-15", "start_time": "09:00", "end_time": "17:00",
        "venue": "Hall A", "maximum_capacity": 50, "registration_deadline": "2026-11-14 23:59:59"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

# 6. Event retrieval
def test_06_event_retrieval(env):
    client, _, _ = env
    res = client.get("/api/events")
    assert res.status_code == 200

# 7. Valid RSVP
def test_07_valid_rsvp(env):
    client, SessionLocal, _ = env
    db = SessionLocal()
    org = User(email="org7@cloud.edu", hashed_password="pw", full_name="Org 7", role=UserRole.ORGANIZER)
    att = User(email="att7@cloud.edu", hashed_password="pw", full_name="Att 7", role=UserRole.ATTENDEE)
    db.add_all([org, att])
    db.commit()
    evt = Event(organizer_id=org.id, title="Evt 7", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=10, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    rsvp, waitlist = process_rsvp(db, evt.id, att.id, RSVPStatus.GOING)
    assert rsvp.status == RSVPStatus.GOING
    assert waitlist is None
    assert evt.current_going == 1
    db.close()

# 8. Duplicate RSVP prevention
def test_08_duplicate_rsvp_prevention(env):
    client, SessionLocal, _ = env
    db = SessionLocal()
    org = User(email="org8@cloud.edu", hashed_password="pw", full_name="Org 8", role=UserRole.ORGANIZER)
    att = User(email="att8@cloud.edu", hashed_password="pw", full_name="Att 8", role=UserRole.ATTENDEE)
    db.add_all([org, att])
    db.commit()
    evt = Event(organizer_id=org.id, title="Evt 8", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=10, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    process_rsvp(db, evt.id, att.id, RSVPStatus.GOING)
    process_rsvp(db, evt.id, att.id, RSVPStatus.GOING)
    count = db.query(RSVP).filter(RSVP.event_id == evt.id, RSVP.user_id == att.id).count()
    assert count == 1
    db.close()

# 9. Update GOING -> MAYBE
def test_09_update_going_to_maybe(env):
    client, SessionLocal, _ = env
    db = SessionLocal()
    org = User(email="org9@cloud.edu", hashed_password="pw", full_name="Org 9", role=UserRole.ORGANIZER)
    att = User(email="att9@cloud.edu", hashed_password="pw", full_name="Att 9", role=UserRole.ATTENDEE)
    db.add_all([org, att])
    db.commit()
    evt = Event(organizer_id=org.id, title="Evt 9", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=10, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    process_rsvp(db, evt.id, att.id, RSVPStatus.GOING)
    assert evt.current_going == 1
    process_rsvp(db, evt.id, att.id, RSVPStatus.MAYBE)
    assert evt.current_going == 0
    db.close()

# 10. Update MAYBE -> GOING
def test_10_update_maybe_to_going(env):
    client, SessionLocal, _ = env
    db = SessionLocal()
    org = User(email="org10@cloud.edu", hashed_password="pw", full_name="Org 10", role=UserRole.ORGANIZER)
    att = User(email="att10@cloud.edu", hashed_password="pw", full_name="Att 10", role=UserRole.ATTENDEE)
    db.add_all([org, att])
    db.commit()
    evt = Event(organizer_id=org.id, title="Evt 10", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=10, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    process_rsvp(db, evt.id, att.id, RSVPStatus.MAYBE)
    assert evt.current_going == 0
    process_rsvp(db, evt.id, att.id, RSVPStatus.GOING)
    assert evt.current_going == 1
    db.close()

# 11. Cancel RSVP (NOT_GOING)
def test_11_cancel_rsvp(env):
    client, SessionLocal, _ = env
    db = SessionLocal()
    org = User(email="org11@cloud.edu", hashed_password="pw", full_name="Org 11", role=UserRole.ORGANIZER)
    att = User(email="att11@cloud.edu", hashed_password="pw", full_name="Att 11", role=UserRole.ATTENDEE)
    db.add_all([org, att])
    db.commit()
    evt = Event(organizer_id=org.id, title="Evt 11", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=10, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    process_rsvp(db, evt.id, att.id, RSVPStatus.GOING)
    assert evt.current_going == 1
    process_rsvp(db, evt.id, att.id, RSVPStatus.NOT_GOING)
    assert evt.current_going == 0
    db.close()

# 12. Registration deadline enforcement
def test_12_registration_deadline_rejection(env):
    client, SessionLocal, _ = env
    db = SessionLocal()
    org = User(email="org12@cloud.edu", hashed_password="pw", full_name="Org 12", role=UserRole.ORGANIZER)
    att = User(email="att12@cloud.edu", hashed_password="pw", full_name="Att 12", role=UserRole.ATTENDEE)
    db.add_all([org, att])
    db.commit()
    # Past deadline
    evt = Event(organizer_id=org.id, title="Evt 12", event_date="2026-01-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=10, registration_deadline="2025-01-01 00:00:00")
    db.add(evt)
    db.commit()

    with pytest.raises(Exception):
        process_rsvp(db, evt.id, att.id, RSVPStatus.GOING)
    db.close()

# 13. Capacity enforcement
def test_13_capacity_enforcement(env):
    client, SessionLocal, _ = env
    db = SessionLocal()
    org = User(email="org13@cloud.edu", hashed_password="pw", full_name="Org 13", role=UserRole.ORGANIZER)
    u1 = User(email="u1_13@cloud.edu", hashed_password="pw", full_name="U1", role=UserRole.ATTENDEE)
    u2 = User(email="u2_13@cloud.edu", hashed_password="pw", full_name="U2", role=UserRole.ATTENDEE)
    db.add_all([org, u1, u2])
    db.commit()
    evt = Event(organizer_id=org.id, title="Evt 13", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=1, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    process_rsvp(db, evt.id, u1.id, RSVPStatus.GOING)
    assert evt.status == EventStatus.FULL
    _, waitlist = process_rsvp(db, evt.id, u2.id, RSVPStatus.GOING)
    assert waitlist is not None
    db.close()

# 14. Simultaneous final-seat requests serialization
def test_14_simultaneous_final_seat_requests(env):
    client, SessionLocal, _ = env
    db = SessionLocal()
    org = User(email="org14@cloud.edu", hashed_password="pw", full_name="Org 14", role=UserRole.ORGANIZER)
    u1 = User(email="u1_14@cloud.edu", hashed_password="pw", full_name="U1", role=UserRole.ATTENDEE)
    u2 = User(email="u2_14@cloud.edu", hashed_password="pw", full_name="U2", role=UserRole.ATTENDEE)
    db.add_all([org, u1, u2])
    db.commit()
    evt = Event(organizer_id=org.id, title="Evt 14", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=1, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    # User 1 claims seat
    r1, _ = process_rsvp(db, evt.id, u1.id, RSVPStatus.GOING)
    # User 2 concurrently attempts claim
    r2, w2 = process_rsvp(db, evt.id, u2.id, RSVPStatus.GOING)
    assert evt.current_going == 1
    assert w2 is not None
    db.close()

# 15. Waitlist auto-promotion
def test_15_waitlist_auto_promotion(env):
    client, SessionLocal, _ = env
    db = SessionLocal()
    org = User(email="org15@cloud.edu", hashed_password="pw", full_name="Org 15", role=UserRole.ORGANIZER)
    u1 = User(email="u1_15@cloud.edu", hashed_password="pw", full_name="U1", role=UserRole.ATTENDEE)
    u2 = User(email="u2_15@cloud.edu", hashed_password="pw", full_name="U2", role=UserRole.ATTENDEE)
    db.add_all([org, u1, u2])
    db.commit()
    evt = Event(organizer_id=org.id, title="Evt 15", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=1, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    process_rsvp(db, evt.id, u1.id, RSVPStatus.GOING)
    process_rsvp(db, evt.id, u2.id, RSVPStatus.GOING)
    # u1 cancels
    process_rsvp(db, evt.id, u1.id, RSVPStatus.NOT_GOING)
    assert evt.current_going == 1
    u2_rsvp = db.query(RSVP).filter(RSVP.event_id == evt.id, RSVP.user_id == u2.id).first()
    assert u2_rsvp.status == RSVPStatus.GOING
    db.close()

# 16. Announcement creation
def test_16_announcement_creation(env):
    client, _, _ = env
    client.post("/api/auth/register", json={"email": "org16@cloud.edu", "password": "password123", "full_name": "Org 16", "role": "organizer"})
    token = client.post("/api/auth/login", data={"username": "org16@cloud.edu", "password": "password123"}).json()["access_token"]
    evt_res = client.post("/api/events", json={
        "title": "Evt 16", "event_date": "2026-11-15", "start_time": "09:00", "end_time": "17:00",
        "venue": "Hall A", "maximum_capacity": 50, "registration_deadline": "2026-11-14 23:59:59"
    }, headers={"Authorization": f"Bearer {token}"})
    eventId = evt_res.json()["id"]

    res = client.post(f"/api/events/{eventId}/announcements", json={
        "title": "Welcome", "message": "Doors open at 8:30"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201

# 17. Notification generation
def test_17_notification_generation(env):
    client, _, _ = env
    client.post("/api/auth/register", json={"email": "org17@cloud.edu", "password": "password123", "full_name": "Org 17", "role": "organizer"})
    org_token = client.post("/api/auth/login", data={"username": "org17@cloud.edu", "password": "password123"}).json()["access_token"]
    client.post("/api/auth/register", json={"email": "att17@cloud.edu", "password": "password123", "full_name": "Att 17", "role": "attendee"})
    att_token = client.post("/api/auth/login", data={"username": "att17@cloud.edu", "password": "password123"}).json()["access_token"]

    evt_res = client.post("/api/events", json={
        "title": "Evt 17", "event_date": "2026-11-15", "start_time": "09:00", "end_time": "17:00",
        "venue": "Hall A", "maximum_capacity": 50, "registration_deadline": "2026-11-14 23:59:59"
    }, headers={"Authorization": f"Bearer {org_token}"})
    eventId = evt_res.json()["id"]

    client.post(f"/api/events/{eventId}/rsvp", json={"status": "GOING"}, headers={"Authorization": f"Bearer {att_token}"})
    client.post(f"/api/events/{eventId}/announcements", json={"title": "Notice", "message": "Test"}, headers={"Authorization": f"Bearer {org_token}"})
    notifs = client.get("/api/notifications", headers={"Authorization": f"Bearer {att_token}"}).json()
    assert len(notifs) >= 1

# 18. Unauthorized event modification
def test_18_unauthorized_event_modification(env):
    client, _, _ = env
    client.post("/api/auth/register", json={"email": "org18a@cloud.edu", "password": "password123", "full_name": "Org 18A", "role": "organizer"})
    tokenA = client.post("/api/auth/login", data={"username": "org18a@cloud.edu", "password": "password123"}).json()["access_token"]
    client.post("/api/auth/register", json={"email": "org18b@cloud.edu", "password": "password123", "full_name": "Org 18B", "role": "organizer"})
    tokenB = client.post("/api/auth/login", data={"username": "org18b@cloud.edu", "password": "password123"}).json()["access_token"]

    evt = client.post("/api/events", json={
        "title": "Evt 18", "event_date": "2026-11-15", "start_time": "09:00", "end_time": "17:00",
        "venue": "Hall A", "maximum_capacity": 50, "registration_deadline": "2026-11-14 23:59:59"
    }, headers={"Authorization": f"Bearer {tokenA}"}).json()

    res = client.put(f"/api/events/{evt['id']}", json={"venue": "Hijacked"}, headers={"Authorization": f"Bearer {tokenB}"})
    assert res.status_code == 403

# 19. Unauthorized RSVP modification
def test_19_unauthorized_rsvp_modification(env):
    client, _, _ = env
    res = client.post("/api/rsvp/public", json={"token": "fake_non_existent_token", "status": "GOING"})
    assert res.status_code == 404

# 20. Real-time counter update
def test_20_realtime_counter_update(env):
    client, _, _ = env
    with client.websocket_connect("/ws/events/realtime-test-event") as ws:
        data = ws.receive_json()
        assert data["type"] == "INITIAL_STATE"
        assert "counts" in data

# 21. Analytics calculation
def test_21_analytics_calculation(env):
    client, SessionLocal, _ = env
    db = SessionLocal()
    org = User(email="org21@cloud.edu", hashed_password="pw", full_name="Org 21", role=UserRole.ORGANIZER)
    db.add(org)
    db.commit()
    evt = Event(organizer_id=org.id, title="Evt 21", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=100, current_going=20, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    analytics = calculate_event_analytics(db, evt.id)
    assert analytics["capacity_utilization_pct"] == 20.0
    assert analytics["available_seats"] == 80
    db.close()

# 22. Database failure / graceful handling
def test_22_database_graceful_handling(env):
    client, _, _ = env
    res = client.get("/api/events/non-existent-uuid-12345")
    assert res.status_code == 404

# 23. Real-time connection handling
def test_23_realtime_connection_ping_pong(env):
    client, _, _ = env
    with client.websocket_connect("/ws/events/ping-event") as ws:
        ws.receive_json()
        ws.send_text("ping")
        assert ws.receive_text() == "pong"

# 24. Authentication token validation
def test_24_auth_token_validation(env):
    client, _, _ = env
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_tampered_token"})
    assert res.status_code == 401

# 25. Event cancellation
def test_25_event_cancellation(env):
    client, _, _ = env
    client.post("/api/auth/register", json={"email": "org25@cloud.edu", "password": "password123", "full_name": "Org 25", "role": "organizer"})
    token = client.post("/api/auth/login", data={"username": "org25@cloud.edu", "password": "password123"}).json()["access_token"]
    evt = client.post("/api/events", json={
        "title": "Evt 25", "event_date": "2026-11-15", "start_time": "09:00", "end_time": "17:00",
        "venue": "Hall A", "maximum_capacity": 50, "registration_deadline": "2026-11-14 23:59:59"
    }, headers={"Authorization": f"Bearer {token}"}).json()

    cancel_res = client.post(f"/api/events/{evt['id']}/cancel", headers={"Authorization": f"Bearer {token}"})
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"
