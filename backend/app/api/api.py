from fastapi import APIRouter
from app.api.routes import tracking, analytics, search, similar_users, health

api_router = APIRouter()

# Register sub-routers
api_router.include_router(health.router, tags=["Health & System Monitor"])
api_router.include_router(tracking.router, tags=["Event Ingestion"])
api_router.include_router(analytics.router, tags=["Analytics Aggregates"])
api_router.include_router(search.router, tags=["Semantic Vector Search"])
api_router.include_router(similar_users.router, tags=["Profile Behavioral Similarity"])
