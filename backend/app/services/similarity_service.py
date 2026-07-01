from typing import List, Dict, Any
import numpy as np
from app.repository.user_repository import UserRepository
from app.repository.event_repository import EventRepository
from app.utils.faiss_manager import FAISSIndexManager
from app.core.logger import logger
from app.core.exceptions import EntityNotFoundException, VectorSearchException

class SimilarityService:
    """
    Computes profile similarity across users based on their historical behavior embeddings.
    """
    def __init__(self, user_repository: UserRepository, event_repository: EventRepository):
        self.user_repo = user_repository
        self.event_repo = event_repository
        self.faiss_manager = FAISSIndexManager()

    async def _get_user_centroid(self, user_id: str) -> np.ndarray:
        """
        Reconstructs all vectors for a user, computes their centroid, and normalizes it.
        """
        mappings = await self.event_repo.get_vector_mappings_for_user(user_id)
        if not mappings:
            return None

        vectors = []
        for mapping in mappings:
            try:
                vec = self.faiss_manager.reconstruct_vector(mapping.vector_index)
                vectors.append(vec)
            except VectorSearchException as e:
                logger.warning(f"Failed to reconstruct vector index {mapping.vector_index}: {e}")
                continue

        if not vectors:
            return None

        # Calculate mean vector (Centroid)
        centroid = np.mean(vectors, axis=0)
        
        # Normalize to unit length
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
            
        return centroid

    async def get_similar_users(self, target_user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves users with behavior profiles most similar to the target user.
        Calculates cosine similarity between user behavior centroids.
        """
        # 1. Verify target user exists
        target_user = await self.user_repo.get_by_id(target_user_id)
        if not target_user:
            raise EntityNotFoundException(f"User with ID '{target_user_id}' does not exist.")

        # 2. Get target user's centroid vector
        target_centroid = await self._get_user_centroid(target_user_id)
        if target_centroid is None:
            # If user has no events or no active embeddings, return empty list
            return []

        # 3. Retrieve all other users in system
        all_users = await self.user_repo.get_all_users()
        similar_users = []

        for user in all_users:
            # Skip the target user
            if user.id == target_user_id:
                continue

            # Compute current comparison user's centroid
            user_centroid = await self._get_user_centroid(user.id)
            if user_centroid is None:
                continue

            # Calculate cosine similarity (dot product of normalized centroids)
            similarity = float(np.dot(target_centroid, user_centroid))
            
            # Map score range bounds [-1.0, 1.0] -> [0.0, 1.0] for presentational clarity
            # Usually users expect scores in 0-100% or 0.0-1.0
            similarity = max(-1.0, min(1.0, similarity))

            similar_users.append({
                "userId": user.id,
                "similarity_score": round(similarity, 4),
                "total_events": user.total_events,
                "last_active": user.last_active.isoformat() if user.last_active else None
            })

        # 4. Sort by score in descending order and return top K
        similar_users.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_users[:limit]
