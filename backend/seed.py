from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.database import SessionLocal, Base, engine
from backend.models import User, UserRole, Event, EventStatus
from cloud.auth_service import get_password_hash

def seed_default_data():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        # Check if default organizer exists
        org = db.query(User).filter(User.email == "organizer@cloud.edu").first()
        if not org:
            org = User(
                email="organizer@cloud.edu",
                hashed_password=get_password_hash("Password123!"),
                full_name="Prof. Cloud",
                role=UserRole.ORGANIZER
            )
            db.add(org)
            db.commit()
            db.refresh(org)

        # Check default attendee
        att = db.query(User).filter(User.email == "attendee@cloud.edu").first()
        if not att:
            att = User(
                email="attendee@cloud.edu",
                hashed_password=get_password_hash("Password123!"),
                full_name="Alex Student",
                role=UserRole.ATTENDEE
            )
            db.add(att)
            db.commit()
            db.refresh(att)

        # Check sample event
        evt = db.query(Event).filter(Event.title == "Cloud Architecture & Real-Time Systems Symposium").first()
        if not evt:
            evt = Event(
                organizer_id=org.id,
                title="Cloud Architecture & Real-Time Systems Symposium",
                description="Hands-on demonstration of serverless, WebSockets, ACID transactions and distributed computing.",
                event_type="hybrid",
                event_date="2026-11-20",
                start_time="10:00",
                end_time="16:00",
                venue="Main Science Hall Room 402 & Live Stream",
                online_link="https://meet.google.com/xyz-cloud-symposium",
                maximum_capacity=10,
                current_going=0,
                registration_deadline="2026-11-19 23:59:59",
                status=EventStatus.PUBLISHED
            )
            db.add(evt)
            db.commit()

    except Exception as e:
        db.rollback()
        print(f"Notice during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_default_data()
    print("Database seeded with default demo accounts and events.")
