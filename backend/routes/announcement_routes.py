from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Announcement, Event, User, UserRole
from backend.schemas import AnnouncementCreate, AnnouncementResponse
from cloud.auth_service import get_current_user, require_role
from cloud.notification_service import fanout_event_notification

router = APIRouter(prefix="/api/events/{event_id}/announcements", tags=["Announcements"])

@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    event_id: str,
    ann_in: AnnouncementCreate,
    current_user: User = Depends(require_role([UserRole.ORGANIZER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    ann = Announcement(
        event_id=event_id,
        title=ann_in.title,
        message=ann_in.message
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)

    # Automatically fan-out notifications to all RSVPed users
    fanout_event_notification(db, event_id, ann_in.title, ann_in.message)

    return ann

@router.get("", response_model=List[AnnouncementResponse])
def get_announcements(event_id: str, db: Session = Depends(get_db)):
    return db.query(Announcement).filter(Announcement.event_id == event_id).order_by(Announcement.created_at.desc()).all()
