import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import User, Event, RSVP, RSVPStatus, EventStatus, UserRole

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_create_user_and_event(db_session):
    organizer = User(
        email="organizer@cloud.edu",
        hashed_password="hashed_pw",
        full_name="Prof. Cloud",
        role=UserRole.ORGANIZER
    )
    db_session.add(organizer)
    db_session.commit()
    db_session.refresh(organizer)

    event = Event(
        organizer_id=organizer.id,
        title="Cloud Computing Symposium 2026",
        description="Hands-on cloud architecture workshop",
        event_type="hybrid",
        event_date="2026-10-15",
        start_time="10:00",
        end_time="17:00",
        venue="Auditorium B & Google Meet",
        maximum_capacity=50,
        registration_deadline="2026-10-14 23:59:59",
        status=EventStatus.PUBLISHED
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.id is not None
    assert event.current_going == 0
    assert event.maximum_capacity == 50
    assert event.organizer.email == "organizer@cloud.edu"
