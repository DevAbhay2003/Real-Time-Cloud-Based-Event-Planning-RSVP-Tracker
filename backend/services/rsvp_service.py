import secrets
from datetime import datetime, timezone
from typing import Tuple, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.models import Event, RSVP, Waitlist, RSVPStatus, EventStatus, WaitlistStatus, User, Notification

def generate_secure_token() -> str:
    return secrets.token_urlsafe(32)

def promote_next_waitlist_user(db: Session, event: Event) -> Optional[Waitlist]:
    """Finds the earliest FIFO waitlist candidate and promotes them to GOING."""
    next_candidate = db.query(Waitlist).filter(
        Waitlist.event_id == event.id,
        Waitlist.status == WaitlistStatus.PENDING
    ).order_by(Waitlist.joined_at.asc()).first()

    if not next_candidate:
        return None

    # Promote candidate to GOING RSVP
    candidate_rsvp = db.query(RSVP).filter(
        RSVP.event_id == event.id,
        RSVP.user_id == next_candidate.user_id
    ).first()

    now_utc = datetime.now(timezone.utc)

    if candidate_rsvp:
        candidate_rsvp.status = RSVPStatus.GOING
        candidate_rsvp.updated_at = now_utc
    else:
        candidate_rsvp = RSVP(
            event_id=event.id,
            user_id=next_candidate.user_id,
            status=RSVPStatus.GOING
        )
        db.add(candidate_rsvp)

    next_candidate.status = WaitlistStatus.PROMOTED
    event.current_going += 1
    if event.current_going >= event.maximum_capacity:
        event.status = EventStatus.FULL

    # Generate Notification
    notif = Notification(
        user_id=next_candidate.user_id,
        event_id=event.id,
        type="WAITLIST_PROMOTED",
        message=f"Good news! A seat opened up for '{event.title}'. Your RSVP has been promoted to GOING."
    )
    db.add(notif)
    db.flush()
    return next_candidate

def process_rsvp(
    db: Session,
    event_id: str,
    user_id: Optional[str],
    new_status: RSVPStatus,
    plus_ones: int = 0,
    guest_name: Optional[str] = None,
    guest_email: Optional[str] = None,
    invite_token: Optional[str] = None
) -> Tuple[Optional[RSVP], Optional[Waitlist]]:
    """
    Executes a concurrency-safe atomic RSVP operation.
    Uses row-level locking where supported (or transactional isolation)
    to eliminate race conditions when checking and decrementing capacity.
    """
    # 1. Lock the event row to serialize concurrent capacity updates
    event_query = db.query(Event).filter(Event.id == event_id)
    if db.bind.dialect.name != "sqlite":
        event_query = event_query.with_for_update()
    event = event_query.first()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    if event.status == EventStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event has been cancelled")

    now_utc = datetime.now(timezone.utc)

    # 2. Check registration deadline
    now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S")
    if event.registration_deadline and now_str > event.registration_deadline:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration deadline has passed")

    # 3. Fetch existing RSVP
    existing_rsvp = None
    if user_id:
        existing_rsvp = db.query(RSVP).filter(RSVP.event_id == event.id, RSVP.user_id == user_id).first()
    elif invite_token:
        existing_rsvp = db.query(RSVP).filter(RSVP.event_id == event.id, RSVP.invite_token == invite_token).first()

    old_status = existing_rsvp.status if existing_rsvp else None
    requested_seats = 1 + plus_ones

    waitlist_entry = None

    if new_status == RSVPStatus.GOING:
        # Check if user was already going
        if old_status == RSVPStatus.GOING:
            # Updating plus ones
            diff = requested_seats - (1 + existing_rsvp.plus_ones)
            if diff > 0 and (event.current_going + diff) > event.maximum_capacity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough capacity for extra guests")
            event.current_going += diff
            existing_rsvp.plus_ones = plus_ones
            existing_rsvp.updated_at = now_utc
        else:
            # Transition to GOING
            if (event.current_going + requested_seats) > event.maximum_capacity:
                # Capacity exceeded: add to Waitlist instead
                if user_id:
                    existing_waitlist = db.query(Waitlist).filter(
                        Waitlist.event_id == event.id,
                        Waitlist.user_id == user_id,
                        Waitlist.status == WaitlistStatus.PENDING
                    ).first()
                    if not existing_waitlist:
                        waitlist_entry = Waitlist(
                            event_id=event.id,
                            user_id=user_id,
                            status=WaitlistStatus.PENDING
                        )
                        db.add(waitlist_entry)
                        db.flush()
                event.status = EventStatus.FULL
                db.commit()
                return existing_rsvp, waitlist_entry
            
            # Seat available
            event.current_going += requested_seats
            if event.current_going >= event.maximum_capacity:
                event.status = EventStatus.FULL

            if existing_rsvp:
                existing_rsvp.status = RSVPStatus.GOING
                existing_rsvp.plus_ones = plus_ones
                existing_rsvp.updated_at = now_utc
            else:
                existing_rsvp = RSVP(
                    event_id=event.id,
                    user_id=user_id,
                    guest_name=guest_name,
                    guest_email=guest_email,
                    invite_token=invite_token,
                    status=RSVPStatus.GOING,
                    plus_ones=plus_ones
                )
                db.add(existing_rsvp)

    else:
        # User is selecting MAYBE or NOT_GOING
        if old_status == RSVPStatus.GOING:
            # Releasing seats
            freed_seats = 1 + (existing_rsvp.plus_ones if existing_rsvp else 0)
            event.current_going = max(0, event.current_going - freed_seats)
            if event.status == EventStatus.FULL and event.current_going < event.maximum_capacity:
                event.status = EventStatus.PUBLISHED

            # Attempt auto-promotion of next waitlisted attendee
            promote_next_waitlist_user(db, event)

        if existing_rsvp:
            existing_rsvp.status = new_status
            existing_rsvp.plus_ones = 0
            existing_rsvp.updated_at = now_utc
        else:
            existing_rsvp = RSVP(
                event_id=event.id,
                user_id=user_id,
                guest_name=guest_name,
                guest_email=guest_email,
                invite_token=invite_token,
                status=new_status,
                plus_ones=0
            )
            db.add(existing_rsvp)

    db.commit()
    db.refresh(event)
    if existing_rsvp:
        db.refresh(existing_rsvp)
    return existing_rsvp, waitlist_entry
