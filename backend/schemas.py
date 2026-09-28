from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from backend.models import UserRole, EventStatus, RSVPStatus, WaitlistStatus

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1)
    role: UserRole = UserRole.ATTENDEE

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class EventCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: Optional[str] = None
    event_type: str = "hybrid"
    event_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$") # YYYY-MM-DD
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")       # HH:MM
    end_time: str = Field(pattern=r"^\d{2}:\d{2}$")         # HH:MM
    venue: str = Field(min_length=2)
    online_link: Optional[str] = None
    maximum_capacity: int = Field(gt=0, default=100)
    registration_deadline: str # YYYY-MM-DD HH:MM:SS

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    event_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    venue: Optional[str] = None
    online_link: Optional[str] = None
    maximum_capacity: Optional[int] = Field(default=None, gt=0)
    registration_deadline: Optional[str] = None
    status: Optional[EventStatus] = None

class EventResponse(BaseModel):
    id: str
    organizer_id: str
    title: str
    description: Optional[str]
    event_type: str
    event_date: str
    start_time: str
    end_time: str
    venue: str
    online_link: Optional[str]
    maximum_capacity: int
    current_going: int
    registration_deadline: str
    status: EventStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RSVPRequest(BaseModel):
    status: RSVPStatus
    plus_ones: int = Field(default=0, ge=0, le=5)

class PublicRSVPRequest(BaseModel):
    token: str
    status: RSVPStatus
    plus_ones: int = Field(default=0, ge=0, le=5)
    guest_name: Optional[str] = None
    guest_email: Optional[EmailStr] = None

class RSVPResponse(BaseModel):
    id: str
    event_id: str
    user_id: Optional[str]
    guest_name: Optional[str]
    guest_email: Optional[str]
    invite_token: Optional[str]
    status: RSVPStatus
    plus_ones: int
    is_checked_in: bool
    checked_in_at: Optional[datetime]
    responded_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InviteeBatchItem(BaseModel):
    name: str
    email: EmailStr
    plus_ones_allowed: int = 0

class InviteeBatchRequest(BaseModel):
    invitees: List[InviteeBatchItem]

class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=2)
    message: str = Field(min_length=2)

class AnnouncementResponse(BaseModel):
    id: str
    event_id: str
    title: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    event_id: Optional[str]
    type: str
    message: str
    read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
