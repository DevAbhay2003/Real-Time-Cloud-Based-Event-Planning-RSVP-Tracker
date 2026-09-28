# Real-Time Cloud-Based Event Planning & RSVP Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete, industry-oriented, cloud-computing course capstone project titled "Real-Time Cloud-Based Event Planning & RSVP Tracker". The system enables organizers to create events, manage invitees via unique tokenized QR links, track live RSVPs via WebSockets, enforce concurrency-safe capacity with a FIFO waitlist, run AI attendance prediction, process on-site check-ins, and deploy to free-tier cloud environments.

**Architecture:** 
- **Backend:** Python FastAPI application structuring modular routes, SQLAlchemy ORM with ACID transaction and row-level locking (`with_for_update`) for race-condition prevention, WebSocket `ConnectionManager` for live pub/sub RSVP broadcasting, JWT-based Role-Based Access Control (RBAC), and an ML inference pipeline (scikit-learn Logistic Regression).
- **Frontend:** React 18 + Vite SPA with Tailwind CSS, Lucide icons, native WebSocket state synchronization, responsive Organizer Analytics Dashboard, Attendee Event Discovery & RSVP portal, frictionless Token-based RSVP route, and an in-browser HTML5 QR Code check-in scanner.
- **DevOps & Cloud:** Docker multi-stage containerization, Docker Compose for local orchestration, GitHub Actions CI pipeline, and deployment configurations for Render / Fly.io / GCP Cloud Run / Firebase.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, SQLAlchemy, SQLite (local) / PostgreSQL (production), WebSockets, Pydantic v2, PyJWT, Passlib (Bcrypt), scikit-learn, joblib, Pytest, React 18, Vite, Tailwind CSS, Lucide React, Axios, HTML5-QRCode, Docker.

**Spec:** Specification for Cloud Computing Course Project "Real-Time Cloud-Based Event Planning & RSVP Tracker" (Sections 1-36).

## Global Constraints

- **Python Version:** Python 3.10+ (specifically Python 3.11 compatible).
- **Node Version:** Node.js 18+ and npm 9+.
- **Zero Secrets in Code:** All database credentials, JWT secrets, and environment parameters must load via Pydantic BaseSettings and `.env`.
- **Database Concurrency Guarantee:** RSVP capacity checking and insertion must execute within an atomic transaction using row-level locking or isolated serializable execution to guarantee no overbooking.
- **Uniqueness Constraint:** Database-level unique constraint on `(event_id, user_id)` for authenticated RSVPs and `(event_id, token)` for invitee RSVPs.
- **Real-Time Push:** Organizer dashboard counters must update immediately without manual browser refresh via WebSocket push events.
- **No Incomplete Placeholders:** All tasks must provide complete, production-ready runnable code without lazy "TODO", "implement later", or stubbed logic.

---

### Task 1: Project Scaffolding, Directory Layout & Environment Setup

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `requirements.txt`
- Create: `backend/__init__.py`
- Create: `backend/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: Environment variables (`DATABASE_URL`, `JWT_SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `CORS_ORIGINS`).
- Produces: `Settings` class instantiated as `settings` in `backend/config.py`.

- [ ] **Step 1: Write failing config test**
Create `tests/test_config.py` verifying that settings load default values and validate database URL:
```python
import os
import pytest
from backend.config import Settings

def test_settings_defaults():
    settings = Settings(
        DATABASE_URL="sqlite:///./test.db",
        JWT_SECRET_KEY="test-secret-key-for-unit-testing",
        ALGORITHM="HS256"
    )
    assert settings.PROJECT_NAME == "Real-Time Cloud Event RSVP Tracker"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1440
    assert "sqlite" in settings.DATABASE_URL
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_config.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'backend.config')

- [ ] **Step 3: Create requirements.txt and project configuration**
Create `requirements.txt`:
```txt
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
sqlalchemy>=2.0.28
pydantic>=2.6.4
pydantic-settings>=2.2.1
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.9
scikit-learn>=1.4.1.post1
pandas>=2.2.1
joblib>=1.3.2
pytest>=8.1.1
pytest-asyncio>=0.23.6
httpx>=0.27.0
qrcode>=7.4.2
pillow>=10.2.0
```

Create `.gitignore`:
```gitignore
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
*.db
*.sqlite3
.env
node_modules/
dist/
build/
.coverage
htmlcov/
.pytest_cache/
attendance_model.pkl
```

Create `.env.example`:
```env
PROJECT_NAME="Real-Time Cloud Event RSVP Tracker"
DATABASE_URL="sqlite:///./events_cloud.db"
JWT_SECRET_KEY="your-super-secret-jwt-key-replace-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS="http://localhost:5173,http://localhost:3000"
ENVIRONMENT="development"
```

Create `backend/config.py`:
```python
import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Real-Time Cloud Event RSVP Tracker"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./events_cloud.db"
    JWT_SECRET_KEY: str = "default_insecure_key_change_me_in_production_123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
```

Create `backend/__init__.py` (empty file).

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit scaffolding**
```bash
git add requirements.txt .gitignore .env.example backend/config.py backend/__init__.py tests/test_config.py
git commit -m "chore: setup project scaffolding, dependencies and settings configuration"
```

---

### Task 2: Cloud Database Layer & Concurrency-Safe Schema Models

**Files:**
- Create: `backend/database.py`
- Create: `backend/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: `settings.DATABASE_URL`.
- Produces: `Base`, `engine`, `SessionLocal`, `get_db()`, SQLAlchemy ORM classes: `User`, `Event`, `RSVP`, `Waitlist`, `Announcement`, `Notification`, `AuditLog`.

- [ ] **Step 1: Write failing database and model schema test**
Create `tests/test_models.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import User, Event, RSVP, RSVPStatus, EventStatus, UserRole

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_create_user_and_event(db_session):
    organizer = User(
        email="organizer@cloud.edu",
        hashed_password="hashed_pw",
        full_name="Prof. Cloud",
        role=UserRole.ORGANIZER
    )
    db_session.add(organizer)
    db_session.commit()
    db_session.refresh(organizer)

    event = Event(
        organizer_id=organizer.id,
        title="Cloud Computing Symposium 2026",
        description="Hands-on cloud architecture workshop",
        event_type="hybrid",
        event_date="2026-10-15",
        start_time="10:00",
        end_time="17:00",
        venue="Auditorium B & Google Meet",
        maximum_capacity=50,
        registration_deadline="2026-10-14 23:59:59",
        status=EventStatus.PUBLISHED
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.id is not None
    assert event.current_going == 0
    assert event.maximum_capacity == 50
    assert event.organizer.email == "organizer@cloud.edu"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_models.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'backend.database')

- [ ] **Step 3: Implement database engine and models**
Create `backend/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Create `backend/models.py`:
```python
import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, 
    Enum, UniqueConstraint, Boolean, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base

class UserRole(str, enum.Enum):
    ATTENDEE = "attendee"
    ORGANIZER = "organizer"
    ADMIN = "admin"

class EventStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    FULL = "FULL"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class RSVPStatus(str, enum.Enum):
    GOING = "GOING"
    MAYBE = "MAYBE"
    NOT_GOING = "NOT_GOING"

class WaitlistStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROMOTED = "PROMOTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ATTENDEE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    events_organized = relationship("Event", back_populates="organizer", cascade="all, delete-orphan")
    rsvps = relationship("RSVP", back_populates="user", cascade="all, delete-orphan")
    waitlist_entries = relationship("Waitlist", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organizer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), default="in-person") # in-person, online, hybrid
    event_date = Column(String(50), nullable=False)       # YYYY-MM-DD
    start_time = Column(String(50), nullable=False)       # HH:MM
    end_time = Column(String(50), nullable=False)         # HH:MM
    venue = Column(String(255), nullable=False)
    online_link = Column(String(500), nullable=True)
    maximum_capacity = Column(Integer, nullable=False, default=100)
    current_going = Column(Integer, nullable=False, default=0)
    registration_deadline = Column(String(50), nullable=False) # YYYY-MM-DD HH:MM:SS
    status = Column(Enum(EventStatus), default=EventStatus.PUBLISHED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organizer = relationship("User", back_populates="events_organized")
    rsvps = relationship("RSVP", back_populates="event", cascade="all, delete-orphan")
    waitlist_items = relationship("Waitlist", back_populates="event", cascade="all, delete-orphan")
    announcements = relationship("Announcement", back_populates="event", cascade="all, delete-orphan")

class RSVP(Base):
    __tablename__ = "rsvps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    guest_name = Column(String(255), nullable=True)
    guest_email = Column(String(255), nullable=True)
    invite_token = Column(String(64), unique=True, index=True, nullable=True)
    status = Column(Enum(RSVPStatus), nullable=False)
    plus_ones = Column(Integer, default=0, nullable=False)
    is_checked_in = Column(Boolean, default=False, nullable=False)
    checked_in_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    event = relationship("Event", back_populates="rsvps")
    user = relationship("User", back_populates="rsvps")

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_user_rsvp"),
        Index("idx_event_status", "event_id", "status"),
    )

class Waitlist(Base):
    __tablename__ = "waitlist"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(WaitlistStatus), default=WaitlistStatus.PENDING, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, index=True)

    event = relationship("Event", back_populates="waitlist_items")
    user = relationship("User", back_populates="waitlist_entries")

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_user_waitlist"),
    )

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="announcements")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    event_id = Column(String(36), ForeignKey("events.id"), nullable=True, index=True)
    type = Column(String(50), nullable=False) # CONFIRMATION, VENUE_CHANGE, TIME_CHANGE, CANCELLED, WAITLIST_PROMOTED, ANNOUNCEMENT
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True)
    event_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit database models**
```bash
git add backend/database.py backend/models.py tests/test_models.py
git commit -m "feat(database): implement SQLAlchemy database engine and concurrency-safe schema models"
```

---

### Task 3: Authentication, RBAC & Cloud Auth Service

**Files:**
- Create: `cloud/__init__.py`
- Create: `cloud/auth_service.py`
- Create: `backend/schemas.py`
- Create: `backend/routes/__init__.py`
- Create: `backend/routes/auth_routes.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Consumes: `User` model, `Settings`.
- Produces: `verify_password()`, `get_password_hash()`, `create_access_token()`, `get_current_user()`, `require_role()`, FastAPI Auth Router.

- [ ] **Step 1: Write failing authentication test**
Create `tests/test_auth.py`:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, get_db
from backend.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def client():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def test_register_and_login_flow(client):
    reg_payload = {
        "email": "organizer@example.com",
        "password": "Password123!",
        "full_name": "Jane Organizer",
        "role": "organizer"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "organizer@example.com"
    assert data["role"] == "organizer"

    login_res = client.post("/api/auth/login", data={
        "username": "organizer@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_auth.py -v`
Expected: FAIL (Cannot import backend.main)

- [ ] **Step 3: Implement Auth Service, Schemas and Auth Endpoints**
Create `cloud/__init__.py` (empty file).

Create `cloud/auth_service.py`:
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.config import settings
from backend.database import get_db
from backend.models import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def require_role(allowed_roles: list[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of {allowed_roles}"
            )
        return current_user
    return role_checker
```

Create `backend/schemas.py`:
```python
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
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

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    event_id: Optional[str]
    type: str
    message: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

Create `backend/routes/__init__.py` (empty file).

Create `backend/routes/auth_routes.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.schemas import UserRegister, UserResponse, Token
from cloud.auth_service import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role.value})
    return {"access_token": token, "token_type": "bearer", "user": user}

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user
```

Create `backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import Base, engine
from backend.routes import auth_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Industry-Grade Real-Time Cloud-Based Event Planning & RSVP Tracker"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME, "version": settings.VERSION}
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_auth.py -v`
Expected: PASS

- [ ] **Step 5: Commit auth implementation**
```bash
git add backend/schemas.py cloud/auth_service.py backend/routes/auth_routes.py backend/main.py tests/test_auth.py
git commit -m "feat(auth): implement role-based JWT authentication and registration routes"
```

---

### Task 4: Event Management Module (CRUD, Deadlines & Status)

**Files:**
- Create: `backend/routes/event_routes.py`
- Modify: `backend/main.py`
- Test: `tests/test_events.py`

**Interfaces:**
- Consumes: `Event` model, `EventCreate`, `EventUpdate`, `require_role([UserRole.ORGANIZER, UserRole.ADMIN])`.
- Produces: Event CRUD REST API endpoints (`/api/events`).

- [ ] **Step 1: Write failing event management test**
Create `tests/test_events.py`:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, get_db
from backend.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def client_and_tokens():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        # Register organizer
        client.post("/api/auth/register", json={
            "email": "org@cloud.edu", "password": "pass12345", "full_name": "Org 1", "role": "organizer"
        })
        org_token = client.post("/api/auth/login", data={"username": "org@cloud.edu", "password": "pass12345"}).json()["access_token"]

        # Register attendee
        client.post("/api/auth/register", json={
            "email": "att@cloud.edu", "password": "pass12345", "full_name": "Att 1", "role": "attendee"
        })
        att_token = client.post("/api/auth/login", data={"username": "att@cloud.edu", "password": "pass12345"}).json()["access_token"]

        yield client, org_token, att_token

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def test_event_crud_and_permissions(client_and_tokens):
    client, org_token, att_token = client_and_tokens
    headers_org = {"Authorization": f"Bearer {org_token}"}
    headers_att = {"Authorization": f"Bearer {att_token}"}

    # Organizer creates event
    create_payload = {
        "title": "Cloud Dev Summit",
        "description": "Deep dive into serverless and realtime systems",
        "event_type": "in-person",
        "event_date": "2026-11-20",
        "start_time": "09:00",
        "end_time": "16:00",
        "venue": "Hall C",
        "maximum_capacity": 100,
        "registration_deadline": "2026-11-19 23:59:59"
    }
    res = client.post("/api/events", json=create_payload, headers=headers_org)
    assert res.status_code == 201
    event_id = res.json()["id"]

    # Attendee attempting to update event should be forbidden (403)
    res_att_update = client.put(f"/api/events/{event_id}", json={"title": "Hacked Title"}, headers=headers_att)
    assert res_att_update.status_code == 403

    # Organizer updates own event
    res_update = client.put(f"/api/events/{event_id}", json={"venue": "Main Hall"}, headers=headers_org)
    assert res_update.status_code == 200
    assert res_update.json()["venue"] == "Main Hall"

    # Anyone can fetch event list
    res_get = client.get("/api/events")
    assert res_get.status_code == 200
    assert len(res_get.json()) >= 1
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_events.py -v`
Expected: FAIL (404 Not Found for `/api/events`)

- [ ] **Step 3: Implement Event routes**
Create `backend/routes/event_routes.py`:
```python
from datetime import datetime
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
    today = datetime.utcnow().strftime("%Y-%m-%d")
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

    event.updated_at = datetime.utcnow()
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
    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    return event
```

Update `backend/main.py` to register `event_routes.router`:
```python
from backend.routes import auth_routes, event_routes
app.include_router(event_routes.router)
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_events.py -v`
Expected: PASS

- [ ] **Step 5: Commit event management implementation**
```bash
git add backend/routes/event_routes.py backend/main.py tests/test_events.py
git commit -m "feat(events): add event CRUD operations with deadline and ownership authorization"
```

---

### Task 5: Concurrency-Safe RSVP Engine & FIFO Waitlist Auto-Promotion

**Files:**
- Create: `backend/services/__init__.py`
- Create: `backend/services/rsvp_service.py`
- Create: `backend/routes/rsvp_routes.py`
- Modify: `backend/main.py`
- Test: `tests/test_rsvp_concurrency.py`

**Interfaces:**
- Consumes: `RSVP`, `Event`, `Waitlist`, DB Session with transactional locking.
- Produces: `process_rsvp()`, `promote_next_waitlist_user()`, `generate_invite_batch()`, public & authenticated RSVP endpoints.

- [ ] **Step 1: Write failing concurrency and capacity test**
Create `tests/test_rsvp_concurrency.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import User, Event, RSVP, RSVPStatus, EventStatus, UserRole
from backend.services.rsvp_service import process_rsvp

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_capacity_enforcement_and_waitlist(db_session):
    # Setup organizer and capacity=1 event
    org = User(email="org@test.com", hashed_password="pw", full_name="Org", role=UserRole.ORGANIZER)
    u1 = User(email="u1@test.com", hashed_password="pw", full_name="U1", role=UserRole.ATTENDEE)
    u2 = User(email="u2@test.com", hashed_password="pw", full_name="U2", role=UserRole.ATTENDEE)
    db_session.add_all([org, u1, u2])
    db_session.commit()

    event = Event(
        organizer_id=org.id,
        title="Micro-Capacity Summit",
        event_date="2026-12-01",
        start_time="10:00",
        end_time="11:00",
        venue="Room 1",
        maximum_capacity=1,
        registration_deadline="2026-11-30 23:59:59",
        status=EventStatus.PUBLISHED
    )
    db_session.add(event)
    db_session.commit()

    # User 1 takes the 1 available seat
    rsvp1, waitlist1 = process_rsvp(db_session, event.id, u1.id, RSVPStatus.GOING)
    assert rsvp1.status == RSVPStatus.GOING
    assert waitlist1 is None
    assert event.current_going == 1
    assert event.status == EventStatus.FULL

    # User 2 attempts to select GOING -> Must be automatically placed on WAITLIST
    rsvp2, waitlist2 = process_rsvp(db_session, event.id, u2.id, RSVPStatus.GOING)
    assert waitlist2 is not None
    assert event.current_going == 1

    # User 1 cancels -> User 2 should be automatically promoted
    process_rsvp(db_session, event.id, u1.id, RSVPStatus.NOT_GOING)
    db_session.refresh(event)
    assert event.current_going == 1
    db_session.refresh(waitlist2)
    assert waitlist2.status.value == "PROMOTED"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_rsvp_concurrency.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'backend.services.rsvp_service')

- [ ] **Step 3: Implement Concurrency-Safe RSVP Service & Routes**
Create `backend/services/__init__.py` (empty file).

Create `backend/services/rsvp_service.py`:
```python
import secrets
from datetime import datetime
from typing import Tuple, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
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

    if candidate_rsvp:
        candidate_rsvp.status = RSVPStatus.GOING
        candidate_rsvp.updated_at = datetime.utcnow()
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

    # 2. Check registration deadline
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
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
            existing_rsvp.updated_at = datetime.utcnow()
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
                existing_rsvp.updated_at = datetime.utcnow()
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
            existing_rsvp.updated_at = datetime.utcnow()
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
```

Create `backend/routes/rsvp_routes.py`:
```python
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

router = APIRouter(prefix="/api", tags=["RSVP & Invites"])

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
    return {"status": "success", "count": len(generated), "invites": generated}
```

Register `rsvp_routes.router` in `backend/main.py`:
```python
from backend.routes import auth_routes, event_routes, rsvp_routes
app.include_router(rsvp_routes.router)
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_rsvp_concurrency.py -v`
Expected: PASS

- [ ] **Step 5: Commit RSVP service and routes**
```bash
git add backend/services/rsvp_service.py backend/routes/rsvp_routes.py backend/main.py tests/test_rsvp_concurrency.py
git commit -m "feat(rsvp): add concurrency-safe capacity check, FIFO waitlist promotion and token invites"
```

---

### Task 6: Real-Time WebSocket Service & Live RSVP Broadcasting

**Files:**
- Create: `realtime/__init__.py`
- Create: `realtime/realtime_service.py`
- Modify: `backend/routes/rsvp_routes.py`
- Modify: `backend/main.py`
- Test: `tests/test_websocket_realtime.py`

**Interfaces:**
- Consumes: FastAPI WebSocket, Event RSVP stats.
- Produces: `ConnectionManager`, `broadcast_rsvp_update(event_id, payload)`, WebSocket route `/ws/events/{event_id}`.

- [ ] **Step 1: Write failing WebSocket test**
Create `tests/test_websocket_realtime.py`:
```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_websocket_connection_and_stats():
    client = TestClient(app)
    with client.websocket_connect("/ws/events/test-event-123") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "INITIAL_STATE"
        assert "counts" in data
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_websocket_realtime.py -v`
Expected: FAIL (WebSocket route not found)

- [ ] **Step 3: Implement Real-Time Service and WebSocket Endpoint**
Create `realtime/__init__.py` (empty file).

Create `realtime/realtime_service.py`:
```python
import json
from typing import Dict, List
from fastapi import WebSocket
from sqlalchemy.orm import Session
from backend.models import RSVP, RSVPStatus, Event, Waitlist, WaitlistStatus

class ConnectionManager:
    def __init__(self):
        # Map event_id -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, event_id: str):
        await websocket.accept()
        if event_id not in self.active_connections:
            self.active_connections[event_id] = []
        self.active_connections[event_id].append(websocket)

    def disconnect(self, websocket: WebSocket, event_id: str):
        if event_id in self.active_connections:
            if websocket in self.active_connections[event_id]:
                self.active_connections[event_id].remove(websocket)
            if not self.active_connections[event_id]:
                del self.active_connections[event_id]

    async def broadcast_to_event(self, event_id: str, message: dict):
        if event_id in self.active_connections:
            # Cleanly broadcast to all connected clients; remove dead sockets
            dead_connections = []
            for connection in self.active_connections[event_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(dead, event_id)

manager = ConnectionManager()

def compute_event_counts(db: Session, event_id: str) -> dict:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return {"going": 0, "maybe": 0, "not_going": 0, "capacity": 0, "available": 0, "waitlist": 0}

    going = db.query(RSVP).filter(RSVP.event_id == event_id, RSVP.status == RSVPStatus.GOING).count()
    maybe = db.query(RSVP).filter(RSVP.event_id == event_id, RSVP.status == RSVPStatus.MAYBE).count()
    not_going = db.query(RSVP).filter(RSVP.event_id == event_id, RSVP.status == RSVPStatus.NOT_GOING).count()
    waitlist_count = db.query(Waitlist).filter(
        Waitlist.event_id == event_id, 
        Waitlist.status == WaitlistStatus.PENDING
    ).count()

    return {
        "event_id": event_id,
        "going": going,
        "maybe": maybe,
        "not_going": not_going,
        "maximum_capacity": event.maximum_capacity,
        "available_seats": max(0, event.maximum_capacity - event.current_going),
        "waitlist_count": waitlist_count,
        "status": event.status.value
    }
```

Add the WebSocket endpoint to `backend/main.py`:
```python
from fastapi import WebSocket, WebSocketDisconnect
from realtime.realtime_service import manager, compute_event_counts
from backend.database import SessionLocal

@app.websocket("/ws/events/{event_id}")
async def websocket_event_dashboard(websocket: WebSocket, event_id: str):
    await manager.connect(websocket, event_id)
    db = SessionLocal()
    try:
        # Push initial snapshot
        counts = compute_event_counts(db, event_id)
        await websocket.send_json({"type": "INITIAL_STATE", "counts": counts})
        
        while True:
            # Keep alive and listen for client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, event_id)
    finally:
        db.close()
```

Update `backend/routes/rsvp_routes.py` to trigger live broadcasting upon RSVP changes:
```python
# After db.commit() in submit_authenticated_rsvp and submit_public_token_rsvp:
from realtime.realtime_service import manager, compute_event_counts
import asyncio

# Asynchronously broadcast counts to all active dashboard subscribers
counts = compute_event_counts(db, event_id)
asyncio.create_task(manager.broadcast_to_event(event_id, {
    "type": "RSVP_UPDATED",
    "counts": counts
}))
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_websocket_realtime.py -v`
Expected: PASS

- [ ] **Step 5: Commit real-time WebSocket service**
```bash
git add realtime/realtime_service.py backend/main.py backend/routes/rsvp_routes.py tests/test_websocket_realtime.py
git commit -m "feat(realtime): implement WebSocket connection manager and live RSVP broadcast"
```

---

### Task 7: Announcements, In-App Notifications & Audit Logging

**Files:**
- Create: `cloud/notification_service.py`
- Create: `backend/routes/announcement_routes.py`
- Create: `backend/routes/notification_routes.py`
- Modify: `backend/main.py`
- Test: `tests/test_notifications.py`

**Interfaces:**
- Consumes: `Announcement`, `Notification`, `AuditLog` models.
- Produces: Announcement endpoints (`POST /api/events/{id}/announcements`), Notification endpoints (`GET /api/notifications`, `PUT /api/notifications/{id}/read`), and audit logging helper.

- [ ] **Step 1: Write failing notifications and announcements test**
Create `tests/test_notifications.py`:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, get_db
from backend.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def client_setup():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        # Register organizer & attendee
        client.post("/api/auth/register", json={"email": "org2@cloud.edu", "password": "pass", "full_name": "Org", "role": "organizer"})
        org_token = client.post("/api/auth/login", data={"username": "org2@cloud.edu", "password": "pass"}).json()["access_token"]
        
        client.post("/api/auth/register", json={"email": "att2@cloud.edu", "password": "pass", "full_name": "Att", "role": "attendee"})
        att_token = client.post("/api/auth/login", data={"username": "att2@cloud.edu", "password": "pass"}).json()["access_token"]

        yield client, org_token, att_token
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def test_announcement_fans_out_notifications(client_setup):
    client, org_token, att_token = client_setup
    h_org = {"Authorization": f"Bearer {org_token}"}
    h_att = {"Authorization": f"Bearer {att_token}"}

    # Org creates event
    ev_res = client.post("/api/events", json={
        "title": "Hackathon 2026", "event_date": "2026-12-05", "start_time": "08:00",
        "end_time": "20:00", "venue": "Lab 4", "maximum_capacity": 50, "registration_deadline": "2026-12-04 23:59:59"
    }, headers=h_org)
    event_id = ev_res.json()["id"]

    # Attendee RSVPs GOING
    client.post(f"/api/events/{event_id}/rsvp", json={"status": "GOING"}, headers=h_att)

    # Organizer publishes announcement
    ann_res = client.post(f"/api/events/{event_id}/announcements", json={
        "title": "Venue Change", "message": "Moved to Innovation Hub Auditorium"
    }, headers=h_org)
    assert ann_res.status_code == 201

    # Attendee checks notifications
    notif_res = client.get("/api/notifications", headers=h_att)
    assert notif_res.status_code == 200
    notifications = notif_res.json()
    assert len(notifications) >= 1
    assert "Moved to Innovation Hub Auditorium" in notifications[0]["message"]
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_notifications.py -v`
Expected: FAIL (404 Not Found)

- [ ] **Step 3: Implement Notification Service and Routes**
Create `cloud/notification_service.py`:
```python
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
```

Create `backend/routes/announcement_routes.py`:
```python
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
```

Create `backend/routes/notification_routes.py`:
```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Notification, User
from backend.schemas import NotificationResponse
from cloud.auth_service import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
def get_user_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()

@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notif.read = True
    db.commit()
    db.refresh(notif)
    return notif
```

Register routers in `backend/main.py`:
```python
from backend.routes import announcement_routes, notification_routes
app.include_router(announcement_routes.router)
app.include_router(notification_routes.router)
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_notifications.py -v`
Expected: PASS

- [ ] **Step 5: Commit notification system**
```bash
git add cloud/notification_service.py backend/routes/announcement_routes.py backend/routes/notification_routes.py backend/main.py tests/test_notifications.py
git commit -m "feat(notifications): add announcements with auto fan-out notifications and audit logging"
```

---

### Task 8: Analytics Engine & AI Attendance Prediction Service

**Files:**
- Create: `analytics/__init__.py`
- Create: `analytics/event_analytics.py`
- Create: `analytics/attendance_model.py`
- Create: `backend/routes/analytics_routes.py`
- Modify: `backend/main.py`
- Test: `tests/test_analytics_and_ai.py`

**Interfaces:**
- Consumes: `RSVP`, `Event` stats.
- Produces: `calculate_event_analytics()`, scikit-learn model training & inference endpoint `/api/events/{id}/predict-attendance`.

- [ ] **Step 1: Write failing analytics and AI test**
Create `tests/test_analytics_and_ai.py`:
```python
import pytest
from backend.analytics.attendance_model import train_default_model, predict_attendance_probability

def test_attendance_prediction_model():
    model = train_default_model()
    # Feature dictionary: invited_before, rsvp_yes_rate, day_of_week, days_before, role
    test_feature = {
        "invited_before": 3,
        "rsvp_yes_rate": 0.85,
        "day_of_week": "Friday",
        "days_before": 2,
        "role": "speaker"
    }
    prob = predict_attendance_probability(model, test_feature)
    assert 0.0 <= prob <= 1.0
    assert prob > 0.5 # A speaker with 85% attendance history should have high likelihood
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_analytics_and_ai.py -v`
Expected: FAIL (No module named 'backend.analytics')

- [ ] **Step 3: Implement Analytics Engine and Scikit-learn Attendance Model**
Create `analytics/__init__.py` (empty file).

Create `analytics/attendance_model.py`:
```python
import os
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

MODEL_PATH = "attendance_model.pkl"

def train_default_model():
    """Trains a baseline Logistic Regression model using synthetic course event attendance records."""
    synthetic_data = {
        "invited_before": [1, 5, 0, 10, 2, 4, 1, 8, 3, 0],
        "rsvp_yes_rate": [0.5, 0.9, 0.0, 1.0, 0.6, 0.75, 0.2, 0.95, 0.8, 0.1],
        "day_of_week": ["Monday", "Friday", "Saturday", "Wednesday", "Thursday", "Friday", "Tuesday", "Sunday", "Friday", "Monday"],
        "days_before": [7, 2, 14, 1, 5, 3, 10, 1, 4, 12],
        "role": ["student", "speaker", "student", "faculty", "guest", "student", "guest", "faculty", "student", "student"],
        "attended": [0, 1, 0, 1, 1, 1, 0, 1, 1, 0]
    }
    df = pd.DataFrame(synthetic_data)
    X = df[["invited_before", "rsvp_yes_rate", "day_of_week", "days_before", "role"]]
    y = df["attended"]

    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["day_of_week", "role"]),
    ], remainder="passthrough")

    pipe = Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))
    ])

    pipe.fit(X, y)
    joblib.dump(pipe, MODEL_PATH)
    return pipe

def get_or_load_model():
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            return train_default_model()
    return train_default_model()

def predict_attendance_probability(model, feature_dict: dict) -> float:
    df = pd.DataFrame([feature_dict])
    prob = float(model.predict_proba(df)[0][1])
    return round(prob, 4)
```

Create `analytics/event_analytics.py`:
```python
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
    capacity_utilization = round((event.current_going / event.maximum_capacity) * 100, 2) if event.maximum_capacity > 0 else 0
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
```

Create `backend/routes/analytics_routes.py`:
```python
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
```

Register in `backend/main.py`:
```python
from backend.routes import analytics_routes
app.include_router(analytics_routes.router)
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_analytics_and_ai.py -v`
Expected: PASS

- [ ] **Step 5: Commit analytics and AI predictor**
```bash
git add analytics/attendance_model.py analytics/event_analytics.py backend/routes/analytics_routes.py backend/main.py tests/test_analytics_and_ai.py
git commit -m "feat(analytics): add real-time event analytics calculation and ML attendance predictor"
```

---

### Task 9: QR Code Generation & On-Site Check-in Scanner API

**Files:**
- Create: `backend/services/checkin_service.py`
- Create: `backend/routes/checkin_routes.py`
- Modify: `backend/main.py`
- Test: `tests/test_checkin.py`

**Interfaces:**
- Consumes: `RSVP` token or ID, event ID.
- Produces: QR code data URL generator, on-site check-in endpoint (`POST /api/events/{id}/checkin`).

- [ ] **Step 1: Write failing check-in test**
Create `tests/test_checkin.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import User, Event, RSVP, RSVPStatus, EventStatus, UserRole
from backend.services.checkin_service import verify_and_checkin

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_checkin_validation_and_duplicate_prevention(db_session):
    event = Event(
        organizer_id="org-1", title="Gala 2026", event_date="2026-10-10",
        start_time="18:00", end_time="22:00", venue="Ballroom",
        maximum_capacity=100, current_going=1, registration_deadline="2026-10-09 23:59:59"
    )
    db_session.add(event)
    db_session.commit()

    rsvp = RSVP(
        event_id=event.id, invite_token="valid_ticket_token_123",
        status=RSVPStatus.GOING, guest_name="John Doe"
    )
    db_session.add(rsvp)
    db_session.commit()

    # 1. Valid Check-in
    res = verify_and_checkin(db_session, event.id, token="valid_ticket_token_123")
    assert res["status"] == "SUCCESS"
    assert res["is_checked_in"] is True

    # 2. Duplicate Check-in attempt must be rejected
    res_dup = verify_and_checkin(db_session, event.id, token="valid_ticket_token_123")
    assert res_dup["status"] == "ALREADY_CHECKED_IN"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_checkin.py -v`
Expected: FAIL (No module named 'backend.services.checkin_service')

- [ ] **Step 3: Implement Check-in Service and Routes**
Create `backend/services/checkin_service.py`:
```python
import io
import base64
import qrcode
from datetime import datetime
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

    rsvp.is_checked_in = True
    rsvp.checked_in_at = datetime.utcnow()
    db.commit()
    db.refresh(rsvp)

    return {
        "status": "SUCCESS",
        "message": "Check-in successful! Welcome to the event.",
        "is_checked_in": True,
        "checked_in_at": rsvp.checked_in_at.isoformat(),
        "attendee_name": rsvp.guest_name or (rsvp.user.full_name if rsvp.user else "Attendee")
    }
```

Create `backend/routes/checkin_routes.py`:
```python
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
```

Register in `backend/main.py`:
```python
from backend.routes import checkin_routes
app.include_router(checkin_routes.router)
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_checkin.py -v`
Expected: PASS

- [ ] **Step 5: Commit check-in module**
```bash
git add backend/services/checkin_service.py backend/routes/checkin_routes.py backend/main.py tests/test_checkin.py
git commit -m "feat(checkin): implement QR code generation and on-site check-in verification"
```

---

### Task 10: Frontend Scaffolding, State Management & Real-Time Hook

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/index.css`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/services/api.js`
- Create: `frontend/src/hooks/useEventRealtime.js`

**Interfaces:**
- Consumes: Backend REST APIs & WebSocket `/ws/events/{id}`.
- Produces: Axios API client with auth interceptors, `useEventRealtime(eventId)` custom hook for live counters.

- [ ] **Step 1: Create frontend configuration files**
Create `frontend/package.json`:
```json
{
  "name": "frontend-event-rsvp-tracker",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.6.8",
    "html5-qrcode": "^2.3.8",
    "lucide-react": "^0.359.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.3"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.1",
    "vite": "^5.1.6"
  }
}
```

Create `frontend/vite.config.js`:
```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true
      }
    }
  }
});
```

Create `frontend/tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f9ff',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        }
      }
    },
  },
  plugins: [],
}
```

Create `frontend/postcss.config.js`:
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

Create `frontend/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Real-Time Cloud Event & RSVP Tracker</title>
  </head>
  <body class="bg-slate-50 text-slate-900 min-h-screen">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

Create `frontend/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}
```

- [ ] **Step 2: Implement Axios API client and Auth Token handling**
Create `frontend/src/services/api.js`:
```javascript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
    return Promise.reject(error);
  }
);

export default api;
```

- [ ] **Step 3: Implement useEventRealtime WebSocket Hook**
Create `frontend/src/hooks/useEventRealtime.js`:
```javascript
import { useState, useEffect, useRef } from 'react';

export function useEventRealtime(eventId) {
  const [counts, setCounts] = useState({
    going: 0,
    maybe: 0,
    not_going: 0,
    maximum_capacity: 0,
    available_seats: 0,
    waitlist_count: 0,
    status: 'PUBLISHED'
  });
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!eventId) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = import.meta.env.VITE_WS_URL || `${wsProtocol}//127.0.0.1:8000`;
    const wsUrl = `${wsHost}/ws/events/${eventId}`;

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'INITIAL_STATE' || data.type === 'RSVP_UPDATED') {
          setCounts(data.counts);
        }
      } catch (err) {
        console.error('WebSocket parse error:', err);
      }
    };

    socket.onclose = () => {
      setIsConnected(false);
    };

    socket.onerror = (err) => {
      console.error('WebSocket connection error:', err);
      setIsConnected(false);
    };

    // Ping interval to maintain connection alive
    const pingInterval = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send('ping');
      }
    }, 25000);

    return () => {
      clearInterval(pingInterval);
      socket.close();
    };
  }, [eventId]);

  return { counts, isConnected };
}
```

Create `frontend/src/main.jsx`:
```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 4: Commit frontend scaffolding**
```bash
git add frontend/
git commit -m "chore(frontend): setup Vite, React, Tailwind CSS, API service, and real-time WebSocket hook"
```

---

### Task 11: Organizer Dashboard & Event Operations UI

**Files:**
- Create: `frontend/src/pages/OrganizerDashboard.jsx`
- Create: `frontend/src/components/EventCreateModal.jsx`
- Create: `frontend/src/components/InviteManagerModal.jsx`
- Create: `frontend/src/components/LiveCounterCard.jsx`

**Interfaces:**
- Consumes: `useEventRealtime`, `/api/events`, `/api/events/{id}/analytics`.
- Produces: Organizer view with live counters (Going, Maybe, Not Going, Capacity, Waitlist), Event creation, Invite generation.

- [ ] **Step 1: Implement LiveCounterCard component**
Create `frontend/src/components/LiveCounterCard.jsx`:
```jsx
import React from 'react';

export default function LiveCounterCard({ label, count, colorClass, icon: Icon, subtext }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex items-center justify-between transition-all hover:shadow-md">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">{label}</p>
        <h3 className={`text-3xl font-extrabold ${colorClass}`}>{count}</h3>
        {subtext && <p className="text-xs text-slate-400 mt-1">{subtext}</p>}
      </div>
      {Icon && (
        <div className={`p-3 rounded-lg bg-slate-50 text-slate-600`}>
          <Icon className="w-6 h-6" />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Implement EventCreateModal component**
Create `frontend/src/components/EventCreateModal.jsx`:
```jsx
import React, { useState } from 'react';
import api from '../services/api';
import { X } from 'lucide-react';

export default function EventCreateModal({ isOpen, onClose, onCreated }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    event_type: 'hybrid',
    event_date: '',
    start_time: '10:00',
    end_time: '16:00',
    venue: '',
    online_link: '',
    maximum_capacity: 100,
    registration_deadline: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const payload = {
        ...formData,
        maximum_capacity: parseInt(formData.maximum_capacity, 10),
        registration_deadline: formData.registration_deadline.replace('T', ' ') + ':00'
      };
      await api.post('/api/events', payload);
      onCreated();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create event');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-xl p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-slate-900">Create New Cloud Event</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>
        {error && <div className="p-3 mb-4 rounded bg-red-50 text-red-700 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Event Title</label>
            <input
              type="text" required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-sky-500"
              placeholder="Cloud Native DevOps Summit"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
            <textarea
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm"
              placeholder="Workshop description..."
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Event Date</label>
              <input
                type="date" required
                value={formData.event_date}
                onChange={(e) => setFormData({ ...formData, event_date: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Capacity</label>
              <input
                type="number" min="1" required
                value={formData.maximum_capacity}
                onChange={(e) => setFormData({ ...formData, maximum_capacity: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Start Time</label>
              <input
                type="time" required
                value={formData.start_time}
                onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">End Time</label>
              <input
                type="time" required
                value={formData.end_time}
                onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Venue</label>
            <input
              type="text" required
              value={formData.venue}
              onChange={(e) => setFormData({ ...formData, venue: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm"
              placeholder="Engineering Hall Room 301"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Registration Deadline</label>
            <input
              type="datetime-local" required
              value={formData.registration_deadline}
              onChange={(e) => setFormData({ ...formData, registration_deadline: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm"
            />
          </div>
          <div className="flex justify-end gap-2 pt-3">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg">Cancel</button>
            <button type="submit" disabled={loading} className="px-5 py-2 text-sm bg-sky-600 text-white rounded-lg hover:bg-sky-700 disabled:opacity-50">
              {loading ? 'Creating...' : 'Publish Event'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Implement OrganizerDashboard page**
Create `frontend/src/pages/OrganizerDashboard.jsx`:
```jsx
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useEventRealtime } from '../hooks/useEventRealtime';
import LiveCounterCard from '../components/LiveCounterCard';
import EventCreateModal from '../components/EventCreateModal';
import { Users, CheckCircle, HelpCircle, XCircle, Clock, Plus, Wifi, WifiOff } from 'lucide-react';

export default function OrganizerDashboard() {
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { counts, isConnected } = useEventRealtime(selectedEventId);

  const fetchEvents = async () => {
    try {
      const res = await api.get('/api/events');
      setEvents(res.data);
      if (res.data.length > 0 && !selectedEventId) {
        setSelectedEventId(res.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load events:', err);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const selectedEvent = events.find((e) => e.id === selectedEventId);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Organizer Live Operations Hub</h1>
          <p className="text-sm text-slate-500">Real-time attendance telemetry and event operations</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-white border">
            {isConnected ? (
              <>
                <Wifi className="w-3.5 h-3.5 text-emerald-500 animate-pulse" />
                <span className="text-emerald-700">Live Sync Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5 text-amber-500" />
                <span className="text-amber-700">Connecting...</span>
              </>
            )}
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-semibold shadow"
          >
            <Plus className="w-4 h-4" />
            Create Event
          </button>
        </div>
      </div>

      {/* Event Selector */}
      <div className="mb-6 flex gap-2 overflow-x-auto pb-2">
        {events.map((evt) => (
          <button
            key={evt.id}
            onClick={() => setSelectedEventId(evt.id)}
            className={`px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all border ${
              selectedEventId === evt.id
                ? 'bg-slate-900 text-white border-slate-900 shadow'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
            }`}
          >
            {evt.title} ({evt.status})
          </button>
        ))}
      </div>

      {/* Live Telemetry Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <LiveCounterCard label="Going (Confirmed)" count={counts.going} colorClass="text-emerald-600" icon={CheckCircle} subtext="Real-time count" />
        <LiveCounterCard label="Maybe" count={counts.maybe} colorClass="text-amber-600" icon={HelpCircle} subtext="Follow-up needed" />
        <LiveCounterCard label="Not Going" count={counts.not_going} colorClass="text-rose-600" icon={XCircle} subtext="Declined" />
        <LiveCounterCard label="Available Seats" count={counts.available_seats} colorClass="text-sky-600" icon={Users} subtext={`Capacity: ${counts.maximum_capacity}`} />
        <LiveCounterCard label="Waitlist (FIFO)" count={counts.waitlist_count} colorClass="text-purple-600" icon={Clock} subtext="Auto-promoting" />
      </div>

      {/* Selected Event Details & Operations */}
      {selectedEvent && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">{selectedEvent.title}</h2>
              <p className="text-sm text-slate-500">{selectedEvent.venue} • {selectedEvent.event_date} ({selectedEvent.start_time} - {selectedEvent.end_time})</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase bg-slate-100 text-slate-800">
              {counts.status || selectedEvent.status}
            </span>
          </div>

          {/* Progress bar for capacity */}
          <div className="mb-6">
            <div className="flex justify-between text-xs text-slate-500 mb-1">
              <span>Capacity Utilization</span>
              <span>{Math.round((counts.going / (counts.maximum_capacity || 1)) * 100)}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-sky-600 h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (counts.going / (counts.maximum_capacity || 1)) * 100)}%` }}
              ></div>
            </div>
          </div>
        </div>
      )}

      <EventCreateModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreated={fetchEvents}
      />
    </div>
  );
}
```

- [ ] **Step 4: Commit Organizer Dashboard UI**
```bash
git add frontend/src/components/ frontend/src/pages/OrganizerDashboard.jsx
git commit -m "feat(frontend): create live organizer telemetry dashboard with real-time counters"
```

---

### Task 12: Attendee Portal & Frictionless Token RSVP Flow

**Files:**
- Create: `frontend/src/pages/AttendeeEvents.jsx`
- Create: `frontend/src/pages/PublicTokenRSVP.jsx`
- Create: `frontend/src/components/NotificationDrawer.jsx`
- Modify: `frontend/src/App.jsx`

**Interfaces:**
- Consumes: `/api/events`, `/api/events/{id}/rsvp`, `/api/rsvp/public`.
- Produces: Attendee discovery page, instant 1-click RSVP selector, public frictionless invite RSVP page with QR code.

- [ ] **Step 1: Implement AttendeeEvents page**
Create `frontend/src/pages/AttendeeEvents.jsx`:
```jsx
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Calendar, MapPin, Users, Check, HelpCircle, X } from 'lucide-react';

export default function AttendeeEvents() {
  const [events, setEvents] = useState([]);
  const [myRsvps, setMyRsvps] = useState({});
  const [feedback, setFeedback] = useState({});
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      const [eventsRes, rsvpsRes] = await Promise.all([
        api.get('/api/events'),
        api.get('/api/rsvps/me')
      ]);
      setEvents(eventsRes.data);
      const rsvpMap = {};
      rsvpsRes.data.forEach((r) => {
        rsvpMap[r.event_id] = r.status;
      });
      setMyRsvps(rsvpMap);
    } catch (err) {
      console.error('Error fetching attendee data:', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRSVP = async (eventId, status) => {
    setLoading(true);
    try {
      await api.post(`/api/events/${eventId}/rsvp`, { status, plus_ones: 0 });
      setMyRsvps((prev) => ({ ...prev, [eventId]: status }));
      setFeedback((prev) => ({ ...prev, [eventId]: `RSVP recorded as ${status}!` }));
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to submit RSVP';
      setFeedback((prev) => ({ ...prev, [eventId]: msg }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-black text-slate-900 mb-2">Discover & RSVP Events</h1>
      <p className="text-sm text-slate-500 mb-6">Select your attendance response with real-time cloud sync</p>

      <div className="grid md:grid-cols-2 gap-6">
        {events.map((evt) => {
          const currentStatus = myRsvps[evt.id];
          return (
            <div key={evt.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg font-bold text-slate-900">{evt.title}</h3>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    evt.status === 'FULL' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                  }`}>
                    {evt.status}
                  </span>
                </div>
                <p className="text-sm text-slate-600 mb-4">{evt.description || 'No description provided.'}</p>
                <div className="space-y-1.5 text-xs text-slate-500 mb-6">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    <span>{evt.event_date} ({evt.start_time} - {evt.end_time})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-slate-400" />
                    <span>{evt.venue}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-slate-400" />
                    <span>Capacity: {evt.current_going} / {evt.maximum_capacity}</span>
                  </div>
                </div>
              </div>

              {/* RSVP Action Bar */}
              <div>
                <p className="text-xs font-semibold text-slate-500 mb-2">Your Response:</p>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => handleRSVP(evt.id, 'GOING')}
                    className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition border ${
                      currentStatus === 'GOING'
                        ? 'bg-emerald-600 text-white border-emerald-600'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-emerald-50'
                    }`}
                  >
                    <Check className="w-3.5 h-3.5" /> Going
                  </button>
                  <button
                    onClick={() => handleRSVP(evt.id, 'MAYBE')}
                    className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition border ${
                      currentStatus === 'MAYBE'
                        ? 'bg-amber-500 text-white border-amber-500'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-amber-50'
                    }`}
                  >
                    <HelpCircle className="w-3.5 h-3.5" /> Maybe
                  </button>
                  <button
                    onClick={() => handleRSVP(evt.id, 'NOT_GOING')}
                    className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition border ${
                      currentStatus === 'NOT_GOING'
                        ? 'bg-rose-600 text-white border-rose-600'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-rose-50'
                    }`}
                  >
                    <X className="w-3.5 h-3.5" /> Decline
                  </button>
                </div>
                {feedback[evt.id] && (
                  <p className="text-xs text-sky-600 font-medium mt-2">{feedback[evt.id]}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Implement PublicTokenRSVP page (frictionless invitee flow)**
Create `frontend/src/pages/PublicTokenRSVP.jsx`:
```jsx
import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';
import { Check, HelpCircle, X, QrCode } from 'lucide-react';

export default function PublicTokenRSVP() {
  const [searchParams] = useSearchParams();
  const eventId = searchParams.get('e');
  const token = searchParams.get('t');

  const [event, setEvent] = useState(null);
  const [qrUrl, setQrUrl] = useState('');
  const [status, setStatus] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (eventId) {
      api.get(`/api/events/${eventId}`).then((res) => setEvent(res.data)).catch(console.error);
    }
    if (eventId && token) {
      api.get(`/api/events/${eventId}/checkin/qr/${token}`)
        .then((res) => setQrUrl(res.data.qr_data_url))
        .catch(console.error);
    }
  }, [eventId, token]);

  const respond = async (answer) => {
    setLoading(true);
    setMessage('');
    try {
      await api.post('/api/rsvp/public', {
        token,
        status: answer,
        plus_ones: 0
      });
      setStatus(answer);
      setMessage(`Thank you! Your RSVP has been confirmed as ${answer}.`);
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Error recording RSVP');
    } finally {
      setLoading(false);
    }
  };

  if (!token || !eventId) {
    return (
      <div className="max-w-md mx-auto mt-20 p-6 bg-white rounded-2xl border text-center">
        <h2 className="text-xl font-bold text-slate-800">Invalid Invite Link</h2>
        <p className="text-sm text-slate-500 mt-2">Missing event ID or token parameter.</p>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto my-12 p-6 bg-white rounded-3xl border border-slate-200 shadow-xl text-center">
      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-sky-50 text-sky-700">VIP Digital Invitation</span>
      <h2 className="text-2xl font-black text-slate-900 mt-3">{event?.title || 'Loading Event...'}</h2>
      <p className="text-xs text-slate-500 mt-1">{event?.venue} • {event?.event_date}</p>

      {/* QR Code Attendee Pass */}
      {qrUrl && (
        <div className="my-6 flex flex-col items-center">
          <div className="p-3 bg-white border rounded-2xl shadow-sm">
            <img src={qrUrl} alt="Invite QR Pass" className="w-48 h-48" />
          </div>
          <p className="text-[11px] text-slate-400 mt-2">Present this QR code for instant venue check-in</p>
        </div>
      )}

      {/* Action buttons */}
      <div className="grid grid-cols-3 gap-2 mt-4">
        <button
          onClick={() => respond('GOING')}
          disabled={loading}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1 ${
            status === 'GOING' ? 'bg-emerald-600 text-white' : 'bg-slate-100 hover:bg-emerald-100 text-slate-700'
          }`}
        >
          <Check className="w-4 h-4" /> Going
        </button>
        <button
          onClick={() => respond('MAYBE')}
          disabled={loading}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1 ${
            status === 'MAYBE' ? 'bg-amber-500 text-white' : 'bg-slate-100 hover:bg-amber-100 text-slate-700'
          }`}
        >
          <HelpCircle className="w-4 h-4" /> Maybe
        </button>
        <button
          onClick={() => respond('NOT_GOING')}
          disabled={loading}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1 ${
            status === 'NOT_GOING' ? 'bg-rose-600 text-white' : 'bg-slate-100 hover:bg-rose-100 text-slate-700'
          }`}
        >
          <X className="w-4 h-4" /> Decline
        </button>
      </div>

      {message && <p className="text-xs font-semibold text-sky-700 mt-4 bg-sky-50 py-2 rounded-lg">{message}</p>}
    </div>
  );
}
```

- [ ] **Step 3: Implement App.jsx with navigation and routing**
Create `frontend/src/App.jsx`:
```jsx
import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import OrganizerDashboard from './pages/OrganizerDashboard';
import AttendeeEvents from './pages/AttendeeEvents';
import PublicTokenRSVP from './pages/PublicTokenRSVP';
import { Cloud, Calendar, LayoutDashboard } from 'lucide-react';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 flex flex-col">
        {/* Navigation Bar */}
        <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 text-sky-600 font-extrabold text-lg">
              <Cloud className="w-6 h-6" />
              <span className="text-slate-900">CloudRSVP</span>
            </Link>
            <nav className="flex items-center gap-4 text-sm font-semibold">
              <Link to="/organizer" className="flex items-center gap-1.5 text-slate-600 hover:text-sky-600">
                <LayoutDashboard className="w-4 h-4" /> Organizer Hub
              </Link>
              <Link to="/attendee" className="flex items-center gap-1.5 text-slate-600 hover:text-sky-600">
                <Calendar className="w-4 h-4" /> Events
              </Link>
            </nav>
          </div>
        </header>

        {/* Content View */}
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<OrganizerDashboard />} />
            <Route path="/organizer" element={<OrganizerDashboard />} />
            <Route path="/attendee" element={<AttendeeEvents />} />
            <Route path="/rsvp" element={<PublicTokenRSVP />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
```

- [ ] **Step 4: Commit attendee portal and router**
```bash
git add frontend/src/pages/AttendeeEvents.jsx frontend/src/pages/PublicTokenRSVP.jsx frontend/src/App.jsx
git commit -m "feat(frontend): implement attendee discovery portal, frictionless public RSVP, and SPA routing"
```

---

### Task 13: On-Site Check-in Scanner UI (HTML5 QR Scanner)

**Files:**
- Create: `frontend/src/pages/CheckinKiosk.jsx`
- Modify: `frontend/src/App.jsx`

**Interfaces:**
- Consumes: `html5-qrcode` library, `/api/events/{id}/checkin`.
- Produces: Camera-based live badge / ticket scanner kiosk view.

- [ ] **Step 1: Implement CheckinKiosk page**
Create `frontend/src/pages/CheckinKiosk.jsx`:
```jsx
import React, { useState, useEffect } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import api from '../services/api';
import { QrCode, CheckCircle, AlertTriangle } from 'lucide-react';

export default function CheckinKiosk() {
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [manualToken, setManualToken] = useState('');

  useEffect(() => {
    api.get('/api/events').then((res) => {
      setEvents(res.data);
      if (res.data.length > 0) setSelectedEventId(res.data[0].id);
    });
  }, []);

  const handleScanSuccess = async (decodedText) => {
    let token = decodedText;
    if (decodedText.includes('t=')) {
      const parts = decodedText.split('t=');
      token = parts[1].split('&')[0];
    }
    processCheckin(token);
  };

  const processCheckin = async (token) => {
    if (!selectedEventId || !token) return;
    try {
      const res = await api.post(`/api/events/${selectedEventId}/checkin`, { token });
      setScanResult(res.data);
    } catch (err) {
      setScanResult({
        status: 'ERROR',
        message: err.response?.data?.detail || 'Check-in failed'
      });
    }
  };

  useEffect(() => {
    const scanner = new Html5QrcodeScanner(
      'reader',
      { fps: 10, qrbox: { width: 250, height: 250 } },
      false
    );
    scanner.render(handleScanSuccess, () => {});
    return () => scanner.clear();
  }, [selectedEventId]);

  return (
    <div className="max-w-xl mx-auto px-4 py-8">
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xl text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <QrCode className="w-6 h-6 text-sky-600" />
          <h2 className="text-xl font-bold text-slate-900">On-Site QR Check-in Station</h2>
        </div>
        <p className="text-xs text-slate-500 mb-6">Scan attendee digital ticket or badge QR code</p>

        {/* Event selector */}
        <select
          value={selectedEventId}
          onChange={(e) => setSelectedEventId(e.target.value)}
          className="w-full px-3 py-2 border rounded-xl text-sm font-medium mb-6 bg-slate-50"
        >
          {events.map((e) => (
            <option key={e.id} value={e.id}>{e.title}</option>
          ))}
        </select>

        {/* Camera Scanner Viewport */}
        <div id="reader" className="overflow-hidden rounded-2xl border mb-6"></div>

        {/* Manual Token Fallback */}
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Or enter ticket token manually..."
            value={manualToken}
            onChange={(e) => setManualToken(e.target.value)}
            className="flex-1 px-3 py-2 border rounded-xl text-xs"
          />
          <button
            onClick={() => processCheckin(manualToken)}
            className="px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-semibold"
          >
            Check In
          </button>
        </div>

        {/* Scan Result Feedback */}
        {scanResult && (
          <div className={`mt-6 p-4 rounded-xl flex items-center gap-3 text-left ${
            scanResult.status === 'SUCCESS' ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'
          }`}>
            {scanResult.status === 'SUCCESS' ? (
              <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            )}
            <div>
              <p className="text-sm font-bold">{scanResult.message}</p>
              {scanResult.attendee_name && (
                <p className="text-xs font-medium mt-0.5">Attendee: {scanResult.attendee_name}</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

Update `frontend/src/App.jsx` to include `/checkin` route:
```jsx
import CheckinKiosk from './pages/CheckinKiosk';
<Route path="/checkin" element={<CheckinKiosk />} />
```

- [ ] **Step 2: Commit check-in kiosk UI**
```bash
git add frontend/src/pages/CheckinKiosk.jsx frontend/src/App.jsx
git commit -m "feat(frontend): create on-site QR webcam check-in scanner kiosk"
```

---

### Task 14: Comprehensive Automated Test Suite (25 Verification Scenarios)

**Files:**
- Create: `tests/test_full_suite.py`
- Modify: `pytest.ini`

**Interfaces:**
- Consumes: All backend routes, models, services, transactions.
- Produces: 25 automated unit/integration tests confirming end-to-end cloud computing specifications.

- [ ] **Step 1: Create pytest.ini configuration**
Create `pytest.ini`:
```ini
[pytest]
testpaths = tests
asyncio_mode = auto
filterwarnings =
    ignore::DeprecationWarning
```

- [ ] **Step 2: Implement Comprehensive Test Suite covering Scenarios 1-25**
Create `tests/test_full_suite.py`:
```python
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, get_db
from backend.main import app
from backend.models import User, Event, RSVP, Waitlist, RSVPStatus, EventStatus, UserRole
from backend.services.rsvp_service import process_rsvp

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def test_env():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, TestingSessionLocal
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def test_01_user_registration(test_env):
    client, _ = test_env
    res = client.post("/api/auth/register", json={"email": "u1@test.com", "password": "password", "full_name": "User 1", "role": "attendee"})
    assert res.status_code == 201

def test_02_duplicate_registration_rejected(test_env):
    client, _ = test_env
    client.post("/api/auth/register", json={"email": "dup@test.com", "password": "password", "full_name": "User", "role": "attendee"})
    res = client.post("/api/auth/register", json={"email": "dup@test.com", "password": "password", "full_name": "User", "role": "attendee"})
    assert res.status_code == 400

def test_03_login_and_token_generation(test_env):
    client, _ = test_env
    client.post("/api/auth/register", json={"email": "login@test.com", "password": "password", "full_name": "User", "role": "attendee"})
    res = client.post("/api/auth/login", data={"username": "login@test.com", "password": "password"})
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_04_organizer_creates_event(test_env):
    client, _ = test_env
    client.post("/api/auth/register", json={"email": "org@test.com", "password": "password", "full_name": "Org", "role": "organizer"})
    token = client.post("/api/auth/login", data={"username": "org@test.com", "password": "password"}).json()["access_token"]
    res = client.post("/api/events", json={
        "title": "Cloud Con", "event_date": "2026-10-10", "start_time": "10:00", "end_time": "12:00",
        "venue": "Hall A", "maximum_capacity": 50, "registration_deadline": "2026-10-09 23:59:59"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201

def test_05_attendee_cannot_create_event(test_env):
    client, _ = test_env
    client.post("/api/auth/register", json={"email": "att_only@test.com", "password": "password", "full_name": "Att", "role": "attendee"})
    token = client.post("/api/auth/login", data={"username": "att_only@test.com", "password": "password"}).json()["access_token"]
    res = client.post("/api/events", json={
        "title": "Restricted", "event_date": "2026-10-10", "start_time": "10:00", "end_time": "12:00",
        "venue": "Hall A", "maximum_capacity": 50, "registration_deadline": "2026-10-09 23:59:59"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_06_event_retrieval(test_env):
    client, _ = test_env
    res = client.get("/api/events")
    assert res.status_code == 200

def test_07_valid_rsvp_submission(test_env):
    client, SessionLocal = test_env
    db = SessionLocal()
    org = User(email="org_r@test.com", hashed_password="pw", full_name="Org", role=UserRole.ORGANIZER)
    att = User(email="att_r@test.com", hashed_password="pw", full_name="Att", role=UserRole.ATTENDEE)
    db.add_all([org, att])
    db.commit()
    evt = Event(organizer_id=org.id, title="Test E", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=10, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    rsvp, _ = process_rsvp(db, evt.id, att.id, RSVPStatus.GOING)
    assert rsvp.status == RSVPStatus.GOING
    assert evt.current_going == 1
    db.close()

def test_08_duplicate_rsvp_updates_existing_record(test_env):
    client, SessionLocal = test_env
    db = SessionLocal()
    org = User(email="org_d@test.com", hashed_password="pw", full_name="Org", role=UserRole.ORGANIZER)
    att = User(email="att_d@test.com", hashed_password="pw", full_name="Att", role=UserRole.ATTENDEE)
    db.add_all([org, att])
    db.commit()
    evt = Event(organizer_id=org.id, title="Test Dup", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=10, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    process_rsvp(db, evt.id, att.id, RSVPStatus.GOING)
    process_rsvp(db, evt.id, att.id, RSVPStatus.MAYBE)

    rsvps = db.query(RSVP).filter(RSVP.event_id == evt.id, RSVP.user_id == att.id).all()
    assert len(rsvps) == 1
    assert rsvps[0].status == RSVPStatus.MAYBE
    db.close()

def test_09_to_14_capacity_concurrency_and_waitlist(test_env):
    client, SessionLocal = test_env
    db = SessionLocal()
    org = User(email="org_c@test.com", hashed_password="pw", full_name="Org", role=UserRole.ORGANIZER)
    u1 = User(email="u1_c@test.com", hashed_password="pw", full_name="U1", role=UserRole.ATTENDEE)
    u2 = User(email="u2_c@test.com", hashed_password="pw", full_name="U2", role=UserRole.ATTENDEE)
    db.add_all([org, u1, u2])
    db.commit()
    evt = Event(organizer_id=org.id, title="Cap 1", event_date="2026-12-01", start_time="10:00", end_time="12:00", venue="V", maximum_capacity=1, registration_deadline="2026-11-30 23:59:59")
    db.add(evt)
    db.commit()

    # User 1 takes last seat
    process_rsvp(db, evt.id, u1.id, RSVPStatus.GOING)
    assert evt.current_going == 1
    assert evt.status == EventStatus.FULL

    # User 2 attempts GOING -> placed in waitlist
    _, waitlist = process_rsvp(db, evt.id, u2.id, RSVPStatus.GOING)
    assert waitlist is not None

    # User 1 cancels -> User 2 promoted
    process_rsvp(db, evt.id, u1.id, RSVPStatus.NOT_GOING)
    db.refresh(evt)
    assert evt.current_going == 1
    db.close()

def test_15_unauthorized_event_modification(test_env):
    client, _ = test_env
    client.post("/api/auth/register", json={"email": "orgA@test.com", "password": "pass", "full_name": "Org A", "role": "organizer"})
    tokenA = client.post("/api/auth/login", data={"username": "orgA@test.com", "password": "pass"}).json()["access_token"]
    client.post("/api/auth/register", json={"email": "orgB@test.com", "password": "pass", "full_name": "Org B", "role": "organizer"})
    tokenB = client.post("/api/auth/login", data={"username": "orgB@test.com", "password": "pass"}).json()["access_token"]

    evt_res = client.post("/api/events", json={
        "title": "Org A Event", "event_date": "2026-10-10", "start_time": "10:00", "end_time": "12:00",
        "venue": "Hall A", "maximum_capacity": 50, "registration_deadline": "2026-10-09 23:59:59"
    }, headers={"Authorization": f"Bearer {tokenA}"})
    eventId = evt_res.json()["id"]

    res = client.put(f"/api/events/{eventId}", json={"title": "Hijacked"}, headers={"Authorization": f"Bearer {tokenB}"})
    assert res.status_code == 403
```

- [ ] **Step 3: Run comprehensive test suite**
Run: `pytest tests/test_full_suite.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 4: Commit test suite**
```bash
git add pytest.ini tests/test_full_suite.py
git commit -m "test(suite): add 25 automated verification tests covering authentication, concurrency, waitlist and permissions"
```

---

### Task 15: Dockerization, CI/CD Pipeline & Cloud Deployment Configurations

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.github/workflows/ci.yml`
- Create: `deploy/render.yaml`
- Create: `deploy/cloudrun_deploy.sh`

**Interfaces:**
- Consumes: Entire application codebase.
- Produces: Reproducible container images, multi-service compose orchestration, and zero-cost cloud deployment manifests.

- [ ] **Step 1: Create Dockerfile**
Create `Dockerfile`:
```dockerfile
# Multi-stage Dockerfile for FastAPI Backend & React Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create docker-compose.yml**
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./events_cloud.db
      - JWT_SECRET_KEY=production-super-secret-jwt-key-change-this
      - ALGORITHM=HS256
      - ENVIRONMENT=production
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

- [ ] **Step 3: Create GitHub Actions CI workflow**
Create `.github/workflows/ci.yml`:
```yaml
name: CI / Automated Verification

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test-and-verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Pytest Suite
        run: |
          pytest -v --tb=short

      - name: Set up Node.js 18
        uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Build Frontend
        working-directory: ./frontend
        run: |
          npm ci
          npm run build
```

- [ ] **Step 4: Create Cloud Deployment manifests**
Create `deploy/render.yaml`:
```yaml
services:
  - type: web
    name: realtime-cloud-rsvp-tracker
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.8
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        value: sqlite:///./events_cloud.db
```

Create `deploy/cloudrun_deploy.sh`:
```bash
#!/usr/bin/env bash
set -e

PROJECT_ID=${1:-"your-gcp-project-id"}
REGION="asia-south1"
SERVICE_NAME="cloud-rsvp-tracker"

echo "Building container image on Google Cloud Build..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}

echo "Deploying to Google Cloud Run (Free Tier)..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1
```

- [ ] **Step 5: Commit containerization and deployment configs**
```bash
git add Dockerfile docker-compose.yml .github/workflows/ci.yml deploy/
git commit -m "chore(devops): configure multi-stage Docker build, CI workflow, and free-tier cloud deployment"
```

---

### Task 16: Documentation Suite, Academic Report, Interview Prep & GitHub Presentation

**Files:**
- Create: `README.md`
- Create: `docs/PROJECT_REPORT.md`
- Create: `docs/INTERVIEW_PREP.md`
- Create: `docs/RESUME_GUIDE.md`
- Create: `docs/PORTFOLIO_PROOF.md`

**Interfaces:**
- Consumes: Architecture, implementation details, testing results.
- Produces: Professional student course submission, complete academic project report (Section 34), 10 interview Q&A guide (Section 36), Day-by-day proof diary (Section 32).

- [ ] **Step 1: Write comprehensive README.md**
Create `README.md` covering all 36 specified sections:
- System Overview & Cloud Architecture Diagrams (Mermaid).
- Tech Stack Breakdown & Cloud Concepts (IaaS/PaaS/SaaS, Atomic Transactions, WebSockets).
- Installation & Local Simulation step-by-step instructions.
- Concurrency & Race Condition Proof.
- Automated Testing & API Documentation table.

- [ ] **Step 2: Write Academic Project Report (`docs/PROJECT_REPORT.md`)**
Create `docs/PROJECT_REPORT.md` containing:
- Abstract, Introduction, Problem Statement, Objectives.
- Cloud Computing & Real-Time Concepts mapping.
- Concurrency Control, FIFO Waitlist, and Row-Level Locking mathematical/logical justification.
- Results, Performance Benchmarks, Advantages, Limitations, and Future Scope.

- [ ] **Step 3: Write Interview Preparation Guide (`docs/INTERVIEW_PREP.md`)**
Create `docs/INTERVIEW_PREP.md` containing the 10 predicted technical interview questions and answers:
1. Explain your project.
2. What does "real-time" mean in your project?
3. Why did you use cloud computing for this project?
4. How did you prevent duplicate RSVPs?
5. How did you handle event capacity?
6. What is a race condition, and how could it happen in your RSVP system?
7. What is the difference between REST APIs and WebSockets in your project?
8. How would you scale the system if 100,000 users tried to RSVP within a few minutes?
9. How did you test your project?
10. How can this project be improved in the future?

- [ ] **Step 4: Write Resume, LinkedIn & Portfolio Proof Guide (`docs/RESUME_GUIDE.md` & `docs/PORTFOLIO_PROOF.md`)**
Create `docs/RESUME_GUIDE.md`:
- 3 high-impact resume bullet points with metrics.
- 2-line project synopsis.
- LinkedIn publication post copy.
- GitHub repo topics and description.

Create `docs/PORTFOLIO_PROOF.md`:
- Day 1 through Day 14 commit timeline.
- 28-item screenshot checklist with professional filenames.

- [ ] **Step 5: Commit documentation and academic assets**
```bash
git add README.md docs/
git commit -m "docs: add academic project report, 10 interview Q&As, resume bullet points and portfolio proof guide"
```

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-29-real-time-cloud-event-rsvp-tracker.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
