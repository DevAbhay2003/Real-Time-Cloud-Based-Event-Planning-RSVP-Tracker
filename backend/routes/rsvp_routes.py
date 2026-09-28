import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, RSVP, Event, RSVPStatus
from backend.schemas import (
    RSVPRequest, RSVPResponse, PublicRSVPRequest, 
    InviteeBatchRequest
)
from cloud.auth_service import get_current_user
from backend.services.rsvp_service import process_rsvp, generate_secure_token
from realtime.realtime_service import manager, compute_event_counts

router = APIRouter(prefix="/api", tags=["RSVP & Invites"])

def _broadcast_event_update(db: Session, event_id: str):
    try:
        counts = compute_event_counts(db, event_id)
        # Only attempt broadcast if an event loop is running
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(manager.broadcast_to_event(event_id, {
                "type": "RSVP_UPDATED",
                "counts": counts
            }))
    except Exception:
        pass

@router.post("/events/{event_id}/rsvp", response_model=RSVPResponse)
def submit_authenticated_rsvp(
    event_id: str,
    rsvp_in: RSVPRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rsvp, waitlist = process_rsvp(
        db=db,
        event_id=event_id,
        user_id=current_user.id,
        new_status=rsvp_in.status,
        plus_ones=rsvp_in.plus_ones
    )
    _broadcast_event_update(db, event_id)

    if waitlist and not rsvp:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Event is at maximum capacity. You have been placed on the FIFO waitlist."
        )
    return rsvp

@router.post("/rsvp/public", response_model=RSVPResponse)
def submit_public_token_rsvp(
    rsvp_in: PublicRSVPRequest,
    db: Session = Depends(get_db)
):
    existing_rsvp = db.query(RSVP).filter(RSVP.invite_token == rsvp_in.token).first()
    if not existing_rsvp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite token")

    rsvp, waitlist = process_rsvp(
        db=db,
        event_id=existing_rsvp.event_id,
        user_id=None,
        new_status=rsvp_in.status,
        plus_ones=rsvp_in.plus_ones,
        invite_token=rsvp_in.token
    )
    _broadcast_event_update(db, existing_rsvp.event_id)
    return rsvp

@router.get("/events/{event_id}/rsvps", response_model=List[RSVPResponse])
def get_event_rsvps(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.organizer_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return db.query(RSVP).filter(RSVP.event_id == event_id).all()

@router.get("/rsvps/me", response_model=List[RSVPResponse])
def get_my_rsvps(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(RSVP).filter(RSVP.user_id == current_user.id).all()

@router.post("/events/{event_id}/invites")
def generate_invite_tokens(
    event_id: str,
    batch_in: InviteeBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.organizer_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    generated = []
    for item in batch_in.invitees:
        token = generate_secure_token()
        rsvp = RSVP(
            event_id=event.id,
            guest_name=item.name,
            guest_email=item.email,
            invite_token=token,
            status=RSVPStatus.MAYBE
        )
        db.add(rsvp)
        generated.append({
            "name": item.name,
            "email": item.email,
            "token": token,
            "rsvp_url": f"/rsvp?e={event.id}&t={token}"
        })
    db.commit()
    _broadcast_event_update(db, event.id)
    return {"status": "success", "count": len(generated), "invites": generated}
