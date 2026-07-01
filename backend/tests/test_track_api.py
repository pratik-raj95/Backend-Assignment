import pytest
import datetime
from sqlalchemy import select
from httpx import AsyncClient
from app.db.models import Event, User

@pytest.mark.asyncio
async def test_track_event_success(client: AsyncClient, db_session):
    """
    Verifies that a valid event tracking payload is accepted and database records are generated.
    """
    payload = {
        "userId": "user_1",
        "event": "user viewed pricing page",
        "metadata": {"page": "/pricing", "browser": "chrome"},
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    response = await client.post("/api/v1/track", json=payload)
    
    assert response.status_code == 202
    res_data = response.json()
    assert res_data["success"] is True
    assert "eventId" in res_data
    assert res_data["message"] == "Event accepted. Embedding generation scheduled."

    # Validate PostgreSQL inserts
    # 1. User check
    user_query = select(User).where(User.id == "user_1")
    user_res = await db_session.execute(user_query)
    user = user_res.scalar_one_or_none()
    assert user is not None
    assert user.total_events == 1

    # 2. Event check
    event_query = select(Event).where(Event.user_id == "user_1")
    event_res = await db_session.execute(event_query)
    event = event_res.scalar_one_or_none()
    assert event is not None
    assert event.event_name == "user viewed pricing page"
    assert event.metadata_["page"] == "/pricing"

@pytest.mark.asyncio
async def test_track_event_validation_error(client: AsyncClient):
    """
    Verifies that invalid payloads are rejected with standard validation schemas.
    """
    # Payload missing userId
    payload = {
        "event": "user viewed pricing page",
        "metadata": {}
    }
    response = await client.post("/api/v1/track", json=payload)
    assert response.status_code == 400
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

@pytest.mark.asyncio
async def test_track_event_size_limit_exceeded(client: AsyncClient):
    """
    Tests that a request payload larger than 1MB is rejected by the middleware.
    """
    large_metadata = {"data": "x" * (1024 * 1024 + 100)}  # Slightly over 1MB
    payload = {
        "userId": "user_large",
        "event": "heavy event",
        "metadata": large_metadata
    }
    response = await client.post("/api/v1/track", json=payload)
    assert response.status_code == 413
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
