import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_websocket_connection_and_stats():
    client = TestClient(app)
    with client.websocket_connect("/ws/events/test-event-123") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "INITIAL_STATE"
        assert "counts" in data
        assert data["counts"]["going"] == 0
        websocket.send_text("ping")
        resp = websocket.receive_text()
        assert resp == "pong"
