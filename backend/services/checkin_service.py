import io
import base64
import qrcode
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.models import RSVP, RSVPStatus, Event

def generate_qr_base64(data: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"

def verify_and_checkin(db: Session, event_id: str, token: str = None, rsvp_id: str = None) -> dict:
    query = db.query(RSVP).filter(RSVP.event_id == event_id)
    if token:
        rsvp = query.filter(RSVP.invite_token == token).first()
    elif rsvp_id:
        rsvp = query.filter(RSVP.id == rsvp_id).first()
    else:
        return {"status": "ERROR", "message": "No identifier provided"}

    if not rsvp:
        return {"status": "INVALID_TICKET", "message": "Ticket not found for this event."}

    if rsvp.status != RSVPStatus.GOING:
        return {"status": "NOT_REGISTERED", "message": f"RSVP status is {rsvp.status.value}, not GOING."}

    if rsvp.is_checked_in:
        return {
            "status": "ALREADY_CHECKED_IN",
            "message": f"Attendee already checked in at {rsvp.checked_in_at}",
            "attendee_name": rsvp.guest_name or (rsvp.user.full_name if rsvp.user else "Attendee")
        }

    now_utc = datetime.now(timezone.utc)
    rsvp.is_checked_in = True
    rsvp.checked_in_at = now_utc
    db.commit()
    db.refresh(rsvp)

    return {
        "status": "SUCCESS",
        "message": "Check-in successful! Welcome to the event.",
        "is_checked_in": True,
        "checked_in_at": rsvp.checked_in_at.isoformat(),
        "attendee_name": rsvp.guest_name or (rsvp.user.full_name if rsvp.user else "Attendee")
    }
