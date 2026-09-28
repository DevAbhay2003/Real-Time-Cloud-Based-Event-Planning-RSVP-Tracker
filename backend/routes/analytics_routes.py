from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Event, User, UserRole
from cloud.auth_service import get_current_user
from analytics.event_analytics import calculate_event_analytics
from analytics.attendance_model import get_or_load_model, predict_attendance_probability

router = APIRouter(prefix="/api/events/{event_id}/analytics", tags=["Analytics & AI"])

class PredictAttendanceRequest(BaseModel):
    invited_before: int = 1
    rsvp_yes_rate: float = 0.8
    day_of_week: str = "Friday"
    days_before: int = 3
    role: str = "student"

@router.get("")
def get_event_metrics(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return calculate_event_analytics(db, event_id)

@router.post("/predict-attendance")
def predict_invitee_attendance(
    event_id: str,
    req: PredictAttendanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    model = get_or_load_model()
    prob = predict_attendance_probability(model, req.model_dump())
    recommendation = "Send normal reminder"
    if prob < 0.4:
        recommendation = "High risk of no-show: Send early confirmation prompt"
    elif prob > 0.8:
        recommendation = "High probability of attending: Reserve seat"

    return {
        "event_id": event_id,
        "attendance_probability": prob,
        "attendance_likelihood_pct": round(prob * 100, 1),
        "recommendation": recommendation
    }
