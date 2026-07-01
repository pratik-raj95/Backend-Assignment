from typing import List, Dict, Any
import numpy as np
from app.repository.event_repository import EventRepository
from app.services.embedding_service import EmbeddingService
from app.utils.faiss_manager import FAISSIndexManager
from app.core.logger import logger

class SearchService:
    """
    Orchestrates semantic vector searches by combining sentence embeddings,
    FAISS index lookups, and relational event mapping.
    """
    def __init__(self, event_repository: EventRepository):
        self.event_repo = event_repository
        self.embedding_service = EmbeddingService()
        self.faiss_manager = FAISSIndexManager()

    async def semantic_search(
        self,
        query: str,
        k: int = 10,
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic search: embedding -> FAISS search -> database fetch -> ranking.
        Filters out matches falling below the cosine similarity threshold.
        """
        if not query.strip():
            return []

        # 1. Generate query embedding
        query_vector = self.embedding_service.generate_embedding(query)

        # 2. Retrieve nearest neighbors from FAISS
        scores, indices = self.faiss_manager.search_vectors(query_vector, k=k)
        if len(indices) == 0:
            return []

        # Filter out FAISS dummy values (-1) that occur if index has fewer items than K
        valid_pairs = [(score, int(idx)) for score, idx in zip(scores, indices) if idx != -1]
        if not valid_pairs:
            return []

        # 3. Retrieve actual events from database mapping
        indices_list = [idx for _, idx in valid_pairs]
        db_events = await self.event_repo.get_events_by_vector_indices(indices_list)
        
        # Build mapping of vector_index -> Event
        event_map = {idx: event for event, idx in db_events}

        # 4. Map, score, filter and rank final results
        ranked_results = []
        for score, idx in valid_pairs:
            # Map inner product to percentage/range [0, 1] for user presentation
            # Cosine similarity ranges from -1 to 1.
            similarity = float(score)
            
            # Apply similarity score threshold filter
            if similarity < threshold:
                continue

            event = event_map.get(idx)
            if event:
                ranked_results.append({
                    "id": str(event.id),
                    "userId": event.user_id,
                    "event": event.event_name,
                    "metadata": event.metadata_,
                    "timestamp": event.timestamp.isoformat(),
                    "similarity_score": round(similarity, 4)
                })

        return ranked_results
