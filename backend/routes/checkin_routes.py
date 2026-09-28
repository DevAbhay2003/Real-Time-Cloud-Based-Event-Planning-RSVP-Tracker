from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, UserRole, Event
from cloud.auth_service import get_current_user, require_role
from backend.services.checkin_service import verify_and_checkin, generate_qr_base64

router = APIRouter(prefix="/api/events/{event_id}/checkin", tags=["On-Site Check-in"])

class CheckinRequest(BaseModel):
    token: str

@router.post("")
def checkin_attendee(
    event_id: str,
    req: CheckinRequest,
    current_user: User = Depends(require_role([UserRole.ORGANIZER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = verify_and_checkin(db, event_id, token=req.token)
    if result["status"] == "INVALID_TICKET":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])
    return result

@router.get("/qr/{token}")
def get_invite_qr(event_id: str, token: str):
    qr_data = f"/rsvp?e={event_id}&t={token}"
    return {"qr_data_url": generate_qr_base64(qr_data), "rsvp_url": qr_data}
