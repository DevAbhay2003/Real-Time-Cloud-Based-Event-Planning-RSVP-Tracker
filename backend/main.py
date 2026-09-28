from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import Base, engine, SessionLocal
from backend.seed import seed_default_data
from backend.routes import (
    auth_routes, event_routes, rsvp_routes, 
    announcement_routes, notification_routes, 
    analytics_routes, checkin_routes
)
from realtime.realtime_service import manager, compute_event_counts

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_default_data()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Industry-Grade Real-Time Cloud-Based Event Planning & RSVP Tracker",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(event_routes.router)
app.include_router(rsvp_routes.router)
app.include_router(announcement_routes.router)
app.include_router(notification_routes.router)
app.include_router(analytics_routes.router)
app.include_router(checkin_routes.router)

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

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME, "version": settings.VERSION}
