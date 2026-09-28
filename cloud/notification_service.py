from sqlalchemy.orm import Session
from backend.models import Notification, RSVP, User, AuditLog

def fanout_event_notification(db: Session, event_id: str, title: str, message: str, notif_type: str = "ANNOUNCEMENT"):
    """Finds all attendees who have RSVPed to this event and delivers an in-app notification."""
    attendee_rsvps = db.query(RSVP).filter(
        RSVP.event_id == event_id,
        RSVP.user_id.isnot(None)
    ).all()

    for rsvp in attendee_rsvps:
        notif = Notification(
            user_id=rsvp.user_id,
            event_id=event_id,
            type=notif_type,
            message=f"[{title}] {message}"
        )
        db.add(notif)
    db.commit()

def log_audit_action(db: Session, user_id: str, action: str, details: str, event_id: str = None, ip_address: str = None):
    log = AuditLog(
        user_id=user_id,
        event_id=event_id,
        action=action,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
