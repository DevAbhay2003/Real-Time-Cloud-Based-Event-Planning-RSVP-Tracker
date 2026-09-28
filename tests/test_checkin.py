import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base
from backend.models import User, Event, RSVP, RSVPStatus, EventStatus, UserRole
from backend.services.checkin_service import verify_and_checkin

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_checkin_validation_and_duplicate_prevention(db_session):
    event = Event(
        organizer_id="org-1", title="Gala 2026", event_date="2026-10-10",
        start_time="18:00", end_time="22:00", venue="Ballroom",
        maximum_capacity=100, current_going=1, registration_deadline="2026-10-09 23:59:59"
    )
    db_session.add(event)
    db_session.commit()

    rsvp = RSVP(
        event_id=event.id, invite_token="valid_ticket_token_123",
        status=RSVPStatus.GOING, guest_name="John Doe"
    )
    db_session.add(rsvp)
    db_session.commit()

    # 1. Valid Check-in
    res = verify_and_checkin(db_session, event.id, token="valid_ticket_token_123")
    assert res["status"] == "SUCCESS"
    assert res["is_checked_in"] is True

    # 2. Duplicate Check-in attempt must be rejected
    res_dup = verify_and_checkin(db_session, event.id, token="valid_ticket_token_123")
    assert res_dup["status"] == "ALREADY_CHECKED_IN"
