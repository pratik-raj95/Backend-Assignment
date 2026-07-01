import asyncio
import uuid
from fastapi import APIRouter, Depends, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db, SessionLocal
from app.repository.event_repository import EventRepository
from app.repository.user_repository import UserRepository
from app.schemas.event import EventTrackRequest, EventTrackResponse
from app.services.embedding_service import EmbeddingService
from app.utils.faiss_manager import FAISSIndexManager
# Removed RedisCache import
from app.core.limiter import limiter
from app.core.logger import logger

router = APIRouter()

async def process_event_embedding_task(event_id: uuid.UUID):
    """
    Background worker task to generate event embeddings, index them in FAISS,
    and persist mappings in PostgreSQL. Incorporates backoff retries.
    """
    max_retries = 3
    base_backoff = 2  # sleep = base_backoff ** attempt * 2 seconds
    
    for attempt in range(max_retries):
        async with SessionLocal() as db_session:
            try:
                event_repo = EventRepository(db_session)
                event = await event_repo.get_by_id(event_id)
                if not event:
                    logger.error(f"Event ID {event_id} not found in background task database search.")
                    return

                # Skip if already processed
                if event.embedding_status:
                    return

                # Compile text representation for semantic search context
                text = event.event_name

                # Generate vector embedding (384 dimensions)
                embedding_service = EmbeddingService()
                vector = embedding_service.generate_embedding(text)

                # Add embedding to FAISS
                faiss_manager = FAISSIndexManager()
                vector_idx = faiss_manager.add_vector(vector)

                # Save coordinate-index to UUID database mapping
                await event_repo.create_vector_mapping(event.id, vector_idx)
                
                # Update status
                await event_repo.update_status(event.id, True)
                
                # Commit all updates inside transaction block
                await db_session.commit()

                # Redis cache invalidation removed
                
                logger.info(f"Successfully processed embedding for event {event_id}. Mapped to FAISS index {vector_idx}.")
                return

            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries} failed to process event {event_id}: {str(e)}")
                await db_session.rollback()

                # Increment retry count in database
                async with SessionLocal() as retry_db:
                    retry_repo = EventRepository(retry_db)
                    await retry_repo.increment_retry(event_id)
                    await retry_db.commit()

                if attempt < max_retries - 1:
                    sleep_time = (base_backoff ** attempt) * 3
                    logger.info(f"Re-scheduling task for event {event_id} in {sleep_time} seconds...")
                    await asyncio.sleep(sleep_time)
                else:
                    logger.critical(f"Embedding task permanently failed for event {event_id} after {max_retries} attempts.")

@router.post(
    "/track", 
    response_model=EventTrackResponse, 
    status_code=status.HTTP_202_ACCEPTED
)
@limiter.limit("60/minute")
async def track_event(
    request: Request,
    payload: EventTrackRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts behavioral events asynchronously.
    Saves event metadata and triggers background vector embedding tasks.
    """
    user_repo = UserRepository(db)
    event_repo = EventRepository(db)

    # 1. Update/Upsert user profile activity and totals
    await user_repo.upsert_user_activity(payload.userId, payload.timestamp)

    # 2. Write event payload
    event = await event_repo.create_event(
        user_id=payload.userId,
        event_name=payload.event,
        metadata=payload.metadata,
        timestamp=payload.timestamp
    )

    # Commit transaction to ensure persistence before spawning thread worker
    await db.commit()

    # 3. Queue asynchronous embedding worker task
    background_tasks.add_task(process_event_embedding_task, event.id)

    return EventTrackResponse(
        success=True,
        eventId=str(event.id),
        message="Event accepted. Embedding generation scheduled."
    )
