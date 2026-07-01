import asyncio
import datetime
import random
import uuid
from sqlalchemy import select
from app.db.database import engine, SessionLocal, Base
from app.db.models import User, Event, VectorMapping
from app.services.embedding_service import EmbeddingService
from app.utils.faiss_manager import FAISSIndexManager
from app.core.logger import logger, setup_logging

# Ingest mock names and templates
USERS = [
    "user_stripe_98",
    "user_openai_01",
    "user_uber_44",
    "user_google_77",
    "user_notion_32",
    "user_airbnb_15",
]

EVENTS_TEMPLATES = [
    ("user viewed pricing page", {"page": "/pricing", "referral": "google"}),
    ("clicked standard signup button", {"page": "/pricing", "tier": "standard"}),
    ("onboarding completion", {"step": 3, "skipped_profile": False}),
    ("opened dashboard workspace", {"workspace_id": "ws_prod_99"}),
    ("configured webhook integration", {"webhook_url": "https://api.stripe.com/v1"}),
    ("user loaded payment settings", {"tab": "billing"}),
    ("billing payment succeeded", {"revenue": 49, "currency": "usd"}),
    ("clicked pro signup button", {"page": "/pricing", "tier": "pro"}),
    ("billing payment failed", {"error": "insufficient_funds"}),
    ("user viewed docs homepage", {"search_query": "sdk"}),
]

async def seed_data():
    setup_logging()
    logger.info("Starting database seeding...")
    
    # 1. Warm up services
    faiss_manager = FAISSIndexManager()
    embedding_service = EmbeddingService()

    # 2. Reset FAISS index before seeding
    logger.info("Wiping existing FAISS index binary...")
    faiss_manager.clear()

    async with engine.begin() as conn:
        logger.info("Recreating database tables...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        # 3. Create Users
        logger.info("Creating user accounts...")
        user_instances = {}
        for uid in USERS:
            user = User(
                id=uid,
                total_events=0,
                last_active=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=random.randint(0, 10))
            )
            session.add(user)
            user_instances[uid] = user
        await session.flush()

        # 4. Generate events over the last 7 days
        logger.info("Generating historical user behavior events...")
        now = datetime.datetime.now(datetime.timezone.utc)
        
        events_to_seed = []
        for i in range(120):  # Generate 120 mock events
            uid = random.choice(USERS)
            evt_name, metadata = random.choice(EVENTS_TEMPLATES)
            
            # Stagger timestamps backward
            timestamp = now - datetime.timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            event = Event(
                id=uuid.uuid4(),
                user_id=uid,
                event_name=evt_name,
                metadata_=metadata,
                timestamp=timestamp,
                embedding_status=False
            )
            
            # Increment user aggregates denormalized columns
            user = user_instances[uid]
            user.total_events += 1
            if user.last_active < timestamp:
                user.last_active = timestamp
                
            session.add(event)
            events_to_seed.append(event)
            
        await session.flush()
        logger.info(f"Successfully staged {len(events_to_seed)} events in PostgreSQL.")

        # 5. Generate embeddings and populate FAISS
        logger.info("Running SentenceTransformers inference and populating FAISS vector index...")
        for j, event in enumerate(events_to_seed):
            try:
                # Use event name as semantic vector representation
                text = event.event_name
                
                # Generate embedding
                vector = embedding_service.generate_embedding(text)
                
                # Add to FAISS and get vector index
                vec_idx = faiss_manager.add_vector(vector)
                
                # Write mapping
                mapping = VectorMapping(
                    id=uuid.uuid4(),
                    event_id=event.id,
                    vector_index=vec_idx
                )
                session.add(mapping)
                
                # Set status as active
                event.embedding_status = True
                
                if (j + 1) % 20 == 0:
                    logger.info(f"Vectorized {j + 1}/{len(events_to_seed)} events...")
                    
            except Exception as e:
                logger.error(f"Error vectorizing event {event.id}: {e}")
                event.embedding_status = False

        await session.commit()
        logger.info("Persistent database and vector mappings committed successfully.")
        logger.info(f"FAISS index size: {faiss_manager.get_total_vectors()} vectors.")
        logger.info("Data seeding operation complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())
