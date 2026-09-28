from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Event, EventStatus, User, UserRole
from backend.schemas import EventCreate, EventUpdate, EventResponse
from cloud.auth_service import get_current_user, require_role

router = APIRouter(prefix="/api/events", tags=["Event Management"])

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_in: EventCreate,
    current_user: User = Depends(require_role([UserRole.ORGANIZER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    if event_in.start_time >= event_in.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time must be strictly earlier than end_time"
        )
    
    event = Event(
        organizer_id=current_user.id,
        title=event_in.title,
        description=event_in.description,
        event_type=event_in.event_type,
        event_date=event_in.event_date,
        start_time=event_in.start_time,
        end_time=event_in.end_time,
        venue=event_in.venue,
        online_link=event_in.online_link,
        maximum_capacity=event_in.maximum_capacity,
        current_going=0,
        registration_deadline=event_in.registration_deadline,
        status=EventStatus.PUBLISHED
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.get("", response_model=List[EventResponse])
def get_events(
    status_filter: Optional[EventStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    if status_filter:
        query = query.filter(Event.status == status_filter)
    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
    return query.order_by(Event.event_date.asc()).all()

@router.get("/upcoming", response_model=List[EventResponse])
def get_upcoming_events(db: Session = Depends(get_db)):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return db.query(Event).filter(
        Event.event_date >= today,
        Event.status.in_([EventStatus.PUBLISHED, EventStatus.FULL])
    ).order_by(Event.event_date.asc()).all()

@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event

@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: str,
    event_in: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    # Ownership or Admin check
    if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this event."
        )

    update_data = event_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    # Recalculate status if capacity changed
    if event.current_going >= event.maximum_capacity and event.status == EventStatus.PUBLISHED:
        event.status = EventStatus.FULL
    elif event.current_going < event.maximum_capacity and event.status == EventStatus.FULL:
        event.status = EventStatus.PUBLISHED

    event.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)
    return event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this event")
    
    db.delete(event)
    db.commit()
    return None

@router.post("/{event_id}/cancel", response_model=EventResponse)
def cancel_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this event")
    
    event.status = EventStatus.CANCELLED
    event.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)
    return event
