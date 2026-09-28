from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models import Event, RSVP, RSVPStatus, Waitlist, WaitlistStatus

def calculate_event_analytics(db: Session, event_id: str) -> dict:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return {}

    total_rsvps = db.query(RSVP).filter(RSVP.event_id == event_id).count()
    going = db.query(RSVP).filter(RSVP.event_id == event_id, RSVP.status == RSVPStatus.GOING).count()
    maybe = db.query(RSVP).filter(RSVP.event_id == event_id, RSVP.status == RSVPStatus.MAYBE).count()
    not_going = db.query(RSVP).filter(RSVP.event_id == event_id, RSVP.status == RSVPStatus.NOT_GOING).count()
    checked_in = db.query(RSVP).filter(RSVP.event_id == event_id, RSVP.is_checked_in == True).count()
    waitlist_count = db.query(Waitlist).filter(
        Waitlist.event_id == event_id, 
        Waitlist.status == WaitlistStatus.PENDING
    ).count()

    # Calculations
    capacity_utilization = round((event.current_going / event.maximum_capacity) * 100, 2) if event.maximum_capacity > 0 else 0.0
    response_rate = round(((going + maybe + not_going) / max(total_rsvps, 1)) * 100, 2)
    checkin_rate = round((checked_in / max(going, 1)) * 100, 2)

    return {
        "event_id": event_id,
        "title": event.title,
        "maximum_capacity": event.maximum_capacity,
        "current_going": event.current_going,
        "available_seats": max(0, event.maximum_capacity - event.current_going),
        "total_responses": total_rsvps,
        "going_count": going,
        "maybe_count": maybe,
        "not_going_count": not_going,
        "waitlist_count": waitlist_count,
        "checked_in_count": checked_in,
        "capacity_utilization_pct": capacity_utilization,
        "response_rate_pct": response_rate,
        "checkin_rate_pct": checkin_rate,
        "status": event.status.value
    }
