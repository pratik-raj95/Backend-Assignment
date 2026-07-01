import pytest
import datetime
from httpx import AsyncClient
from app.db.models import Event, User

async def seed_events(db_session):
    """
    Helper fixture-like method to seed events with different dates and names.
    """
    # Create Users
    user1 = User(id="user_abc", total_events=3, last_active=datetime.datetime(2026, 1, 10, tzinfo=datetime.timezone.utc))
    user2 = User(id="user_xyz", total_events=1, last_active=datetime.datetime(2026, 1, 12, tzinfo=datetime.timezone.utc))
    db_session.add_all([user1, user2])
    await db_session.flush()

    # Create Events
    ev1 = Event(
        user_id="user_abc",
        event_name="click",
        metadata_={"target": "submit"},
        timestamp=datetime.datetime(2026, 1, 1, 12, 0, tzinfo=datetime.timezone.utc),
        embedding_status=True
    )
    ev2 = Event(
        user_id="user_abc",
        event_name="view",
        metadata_={"page": "pricing"},
        timestamp=datetime.datetime(2026, 1, 2, 14, 0, tzinfo=datetime.timezone.utc),
        embedding_status=True
    )
    ev3 = Event(
        user_id="user_abc",
        event_name="click",
        metadata_={"target": "pricing-btn"},
        timestamp=datetime.datetime(2026, 1, 3, 10, 0, tzinfo=datetime.timezone.utc),
        embedding_status=True
    )
    ev4 = Event(
        user_id="user_xyz",
        event_name="click",
        metadata_={"target": "home-link"},
        timestamp=datetime.datetime(2026, 1, 2, 9, 0, tzinfo=datetime.timezone.utc),
        embedding_status=True
    )
    
    db_session.add_all([ev1, ev2, ev3, ev4])
    await db_session.commit()

@pytest.mark.asyncio
async def test_analytics_no_filters(client: AsyncClient, db_session):
    """
    Verifies base aggregates returned when query params are omitted.
    """
    await seed_events(db_session)

    response = await client.get("/api/v1/analytics")
    assert response.status_code == 200
    data = response.json()

    assert data["totalEvents"] == 4
    assert data["eventsPerUser"]["user_abc"] == 3
    assert data["eventsPerUser"]["user_xyz"] == 1
    
    # Check most active users ranking
    active_users = data["mostActiveUsers"]
    assert len(active_users) == 2
    assert active_users[0]["userId"] == "user_abc"
    assert active_users[0]["count"] == 3
    assert active_users[1]["userId"] == "user_xyz"
    assert active_users[1]["count"] == 1

@pytest.mark.asyncio
async def test_analytics_with_event_filter(client: AsyncClient, db_session):
    """
    Validates filtering analytics metrics by event name.
    """
    await seed_events(db_session)

    response = await client.get("/api/v1/analytics?event=click")
    assert response.status_code == 200
    data = response.json()

    assert data["totalEvents"] == 3  # 3 clicks, 1 view
    assert "user_xyz" in data["eventsPerUser"]
    assert "user_abc" in data["eventsPerUser"]

@pytest.mark.asyncio
async def test_analytics_with_date_range(client: AsyncClient, db_session):
    """
    Validates filtering analytics metrics using date boundaries.
    """
    await seed_events(db_session)

    # Dates covering Jan 1 and Jan 2
    response = await client.get("/api/v1/analytics?from=2026-01-01&to=2026-01-02")
    assert response.status_code == 200
    data = response.json()

    # ev1 (Jan 1), ev2 (Jan 2), ev4 (Jan 2) should match. ev3 (Jan 3) skipped.
    assert data["totalEvents"] == 3

@pytest.mark.asyncio
async def test_analytics_invalid_range_error(client: AsyncClient):
    """
    Verifies validation errors are raised when bounds are inverted.
    """
    response = await client.get("/api/v1/analytics?from=2026-01-05&to=2026-01-01")
    assert response.status_code == 400
    assert response.json()["success"] is False
    assert "from" in response.json()["error"]["message"]
