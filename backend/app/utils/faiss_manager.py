import os
import threading
import numpy as np
import faiss
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import VectorSearchException

class FAISSIndexManager:
    """
    Thread-safe persistent manager for the FAISS vector index.
    Uses IndexFlatIP (Inner Product) with L2 normalized vectors to perform Cosine Similarity.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(FAISSIndexManager, cls).__new__(cls, *args, **kwargs)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.dimension = 384  # MiniLM-L6-v2 output dimension
        self.index_path = settings.FAISS_INDEX_PATH
        self.lock = threading.Lock()
        self.index = None
        
        # Load or create index
        self._load_or_create()
        self._initialized = True

    def _load_or_create(self):
        """
        Loads the index from disk or initializes a blank IndexFlatIP if missing.
        """
        with self.lock:
            # Ensure the directory exists
            directory = os.path.dirname(self.index_path)
            if directory:
                os.makedirs(directory, exist_ok=True)

            if os.path.exists(self.index_path):
                try:
                    logger.info(f"Loading existing FAISS index from {self.index_path}...")
                    self.index = faiss.read_index(self.index_path)
                    logger.info(f"Successfully loaded FAISS index with {self.index.ntotal} vectors.")
                except Exception as e:
                    logger.error(f"Failed to load FAISS index from disk: {e}. Reinitializing index.")
                    self.index = faiss.IndexFlatIP(self.dimension)
            else:
                logger.info(f"No FAISS index found at {self.index_path}. Creating a blank IndexFlatIP index.")
                self.index = faiss.IndexFlatIP(self.dimension)

    def save(self) -> None:
        """
        Serializes the index to disk.
        """
        with self.lock:
            try:
                faiss.write_index(self.index, self.index_path)
                logger.info(f"Saved FAISS index to {self.index_path}. Total vectors: {self.index.ntotal}.")
            except Exception as e:
                logger.error(f"Failed to save FAISS index to disk: {e}.")
                raise VectorSearchException(f"Failed to persist vector index: {e}")

    def add_vector(self, vector: np.ndarray) -> int:
        """
        Normalizes and adds a 384-dimensional vector to the index.
        Returns the index location of the newly added vector.
        """
        if vector.shape != (self.dimension,):
            raise VectorSearchException(
                f"Invalid vector shape. Expected {(self.dimension,)}, got {vector.shape}"
            )

        with self.lock:
            try:
                # L2 Normalize vector for cosine similarity
                norm = np.linalg.norm(vector)
                if norm > 0:
                    normalized_vector = vector / norm
                else:
                    normalized_vector = vector

                # Reshape to (1, dimension) for FAISS input
                data = np.ascontiguousarray(normalized_vector.reshape(1, -1).astype("float32"))
                
                # Get the index where this vector will be inserted
                vector_idx = self.index.ntotal
                
                # Add vector
                self.index.add(data)
                
                # Persist changes
                faiss.write_index(self.index, self.index_path)
                
                return vector_idx
            except Exception as e:
                logger.error(f"Error adding vector to FAISS: {e}")
                raise VectorSearchException(f"FAISS add vector operation failed: {e}")

    def search_vectors(self, query_vector: np.ndarray, k: int = 10) -> tuple[np.ndarray, np.ndarray]:
        """
        Searches the nearest K neighbors using cosine similarity.
        Returns (similarity_scores, vector_indices).
        """
        if query_vector.shape != (self.dimension,):
            raise VectorSearchException(
                f"Invalid query vector shape. Expected {(self.dimension,)}, got {query_vector.shape}"
            )

        with self.lock:
            if self.index.ntotal == 0:
                return np.array([]), np.array([])
                
            try:
                # Normalize query vector
                norm = np.linalg.norm(query_vector)
                if norm > 0:
                    normalized_query = query_vector / norm
                else:
                    normalized_query = query_vector

                data = np.ascontiguousarray(normalized_query.reshape(1, -1).astype("float32"))
                
                # Search FAISS
                scores, indices = self.index.search(data, k)
                return scores[0], indices[0]
            except Exception as e:
                logger.error(f"Error performing vector search in FAISS: {e}")
                raise VectorSearchException(f"FAISS search operation failed: {e}")

    def reconstruct_vector(self, index_id: int) -> np.ndarray:
        """
        Reconstructs the original normalized vector coordinate array by index offset.
        """
        with self.lock:
            try:
                if index_id < 0 or index_id >= self.index.ntotal:
                    raise VectorSearchException(f"Index ID {index_id} is out of bounds (ntotal: {self.index.ntotal})")
                return self.index.reconstruct(index_id)
            except Exception as e:
                logger.error(f"Error reconstructing vector {index_id}: {e}")
                raise VectorSearchException(f"FAISS reconstruction failed: {e}")

    def get_total_vectors(self) -> int:
        """
        Returns the count of vectors currently inside the index.
        """
        with self.lock:
            return self.index.ntotal

    def clear(self) -> None:
        """
        Resets and wipes the FAISS index (mainly used for testing clean states).
        """
        with self.lock:
            self.index = faiss.IndexFlatIP(self.dimension)
            if os.path.exists(self.index_path):
                try:
                    os.remove(self.index_path)
                except Exception:
                    pass
