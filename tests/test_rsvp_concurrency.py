import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base
from backend.models import User, Event, RSVP, RSVPStatus, EventStatus, UserRole
from backend.services.rsvp_service import process_rsvp

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

def test_capacity_enforcement_and_waitlist(db_session):
    # Setup organizer and capacity=1 event
    org = User(email="org@test.com", hashed_password="pw", full_name="Org", role=UserRole.ORGANIZER)
    u1 = User(email="u1@test.com", hashed_password="pw", full_name="U1", role=UserRole.ATTENDEE)
    u2 = User(email="u2@test.com", hashed_password="pw", full_name="U2", role=UserRole.ATTENDEE)
    db_session.add_all([org, u1, u2])
    db_session.commit()

    event = Event(
        organizer_id=org.id,
        title="Micro-Capacity Summit",
        event_date="2026-12-01",
        start_time="10:00",
        end_time="11:00",
        venue="Room 1",
        maximum_capacity=1,
        registration_deadline="2026-11-30 23:59:59",
        status=EventStatus.PUBLISHED
    )
    db_session.add(event)
    db_session.commit()

    # User 1 takes the 1 available seat
    rsvp1, waitlist1 = process_rsvp(db_session, event.id, u1.id, RSVPStatus.GOING)
    assert rsvp1.status == RSVPStatus.GOING
    assert waitlist1 is None
    assert event.current_going == 1
    assert event.status == EventStatus.FULL

    # User 2 attempts to select GOING -> Must be automatically placed on WAITLIST
    rsvp2, waitlist2 = process_rsvp(db_session, event.id, u2.id, RSVPStatus.GOING)
    assert waitlist2 is not None
    assert event.current_going == 1

    # User 1 cancels -> User 2 should be automatically promoted
    process_rsvp(db_session, event.id, u1.id, RSVPStatus.NOT_GOING)
    db_session.refresh(event)
    assert event.current_going == 1
    db_session.refresh(waitlist2)
    assert waitlist2.status.value == "PROMOTED"
