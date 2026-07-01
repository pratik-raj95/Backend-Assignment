import pytest
import datetime
from httpx import AsyncClient
from app.db.models import Event, User, VectorMapping
from app.utils.faiss_manager import FAISSIndexManager
from app.services.embedding_service import EmbeddingService

async def seed_vector_events(db_session):
    """
    Helper to seed events and write their mock embeddings directly to the FAISS test file index.
    """
    # 1. Create Users
    u1 = User(id="user_1", total_events=2)
    u2 = User(id="user_2", total_events=1)
    db_session.add_all([u1, u2])
    await db_session.flush()

    # 2. Create Events
    ev1 = Event(
        user_id="user_1",
        event_name="pricing page view",
        metadata_={"price": "standard"},
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        embedding_status=True
    )
    ev2 = Event(
        user_id="user_1",
        event_name="checkout completion",
        metadata_={"revenue": 49},
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        embedding_status=True
    )
    ev3 = Event(
        user_id="user_2",
        event_name="pricing page view",
        metadata_={"price": "pro"},
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        embedding_status=True
    )
    db_session.add_all([ev1, ev2, ev3])
    await db_session.flush()

    # 3. Add to FAISS index and create Database mappings
    faiss_manager = FAISSIndexManager()
    embedding_service = EmbeddingService()
    
    for ev in [ev1, ev2, ev3]:
        # Generate mock vector coordinates using our mocked service
        vec = embedding_service.generate_embedding(ev.event_name)
        idx = faiss_manager.add_vector(vec)
        
        mapping = VectorMapping(event_id=ev.id, vector_index=idx)
        db_session.add(mapping)
        
    await db_session.commit()

@pytest.mark.asyncio
async def test_semantic_search_success(client: AsyncClient, db_session):
    """
    Verifies that semantic search resolves queries to database event structures.
    """
    await seed_vector_events(db_session)

    # Query matching 'pricing page view'
    response = await client.get("/api/v1/search?query=pricing&threshold=0.5")
    assert response.status_code == 200
    
    data = response.json()
    assert "results" in data
    results = data["results"]
    
    # Check that matched items exist and are sorted by score
    assert len(results) > 0
    assert results[0]["event"] == "pricing page view"
    assert "similarity_score" in results[0]
    assert results[0]["similarity_score"] >= 0.5

@pytest.mark.asyncio
async def test_similar_users_success(client: AsyncClient, db_session):
    """
    Verifies cosine similarity calculations between user profile centroids.
    """
    await seed_vector_events(db_session)

    # Fetch users similar to user_1
    response = await client.get("/api/v1/similar-users?userId=user_1")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["userId"] == "user_2"
    assert "similarity_score" in data[0]

@pytest.mark.asyncio
async def test_similar_users_not_found(client: AsyncClient):
    """
    Ensures requesting similar users for an invalid ID returns a 404 error response.
    """
    response = await client.get("/api/v1/similar-users?userId=user_nonexistent")
    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "NOT_FOUND"
