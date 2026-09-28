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
        return {"event_id": event_id, "going": 0, "maybe": 0, "not_going": 0, "maximum_capacity": 0, "available_seats": 0, "waitlist_count": 0, "status": "UNKNOWN"}

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
