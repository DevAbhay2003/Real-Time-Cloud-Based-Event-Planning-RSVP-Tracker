import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, 
    Enum, UniqueConstraint, Boolean, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    ATTENDEE = "attendee"
    ORGANIZER = "organizer"
    ADMIN = "admin"

class EventStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    FULL = "FULL"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class RSVPStatus(str, enum.Enum):
    GOING = "GOING"
    MAYBE = "MAYBE"
    NOT_GOING = "NOT_GOING"

class WaitlistStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROMOTED = "PROMOTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ATTENDEE, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    events_organized = relationship("Event", back_populates="organizer", cascade="all, delete-orphan")
    rsvps = relationship("RSVP", back_populates="user", cascade="all, delete-orphan")
    waitlist_entries = relationship("Waitlist", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organizer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), default="in-person") # in-person, online, hybrid
    event_date = Column(String(50), nullable=False)       # YYYY-MM-DD
    start_time = Column(String(50), nullable=False)       # HH:MM
    end_time = Column(String(50), nullable=False)         # HH:MM
    venue = Column(String(255), nullable=False)
    online_link = Column(String(500), nullable=True)
    maximum_capacity = Column(Integer, nullable=False, default=100)
    current_going = Column(Integer, nullable=False, default=0)
    registration_deadline = Column(String(50), nullable=False) # YYYY-MM-DD HH:MM:SS
    status = Column(Enum(EventStatus), default=EventStatus.PUBLISHED, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    organizer = relationship("User", back_populates="events_organized")
    rsvps = relationship("RSVP", back_populates="event", cascade="all, delete-orphan")
    waitlist_items = relationship("Waitlist", back_populates="event", cascade="all, delete-orphan")
    announcements = relationship("Announcement", back_populates="event", cascade="all, delete-orphan")

class RSVP(Base):
    __tablename__ = "rsvps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    guest_name = Column(String(255), nullable=True)
    guest_email = Column(String(255), nullable=True)
    invite_token = Column(String(64), unique=True, index=True, nullable=True)
    status = Column(Enum(RSVPStatus), nullable=False)
    plus_ones = Column(Integer, default=0, nullable=False)
    is_checked_in = Column(Boolean, default=False, nullable=False)
    checked_in_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    event = relationship("Event", back_populates="rsvps")
    user = relationship("User", back_populates="rsvps")

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_user_rsvp"),
        Index("idx_event_status", "event_id", "status"),
    )

class Waitlist(Base):
    __tablename__ = "waitlist"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(WaitlistStatus), default=WaitlistStatus.PENDING, nullable=False)
    joined_at = Column(DateTime, default=utc_now, index=True)

    event = relationship("Event", back_populates="waitlist_items")
    user = relationship("User", back_populates="waitlist_entries")

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_user_waitlist"),
    )

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    event = relationship("Event", back_populates="announcements")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    event_id = Column(String(36), ForeignKey("events.id"), nullable=True, index=True)
    type = Column(String(50), nullable=False) # CONFIRMATION, VENUE_CHANGE, TIME_CHANGE, CANCELLED, WAITLIST_PROMOTED, ANNOUNCEMENT
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="notifications")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True)
    event_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=utc_now)
