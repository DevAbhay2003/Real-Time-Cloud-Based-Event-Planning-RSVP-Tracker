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
    assert len(settings.cors_origins_list) > 0
