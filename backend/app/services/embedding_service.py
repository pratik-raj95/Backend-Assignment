import threading
import numpy as np
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import EmbeddingGenerationException

class EmbeddingService:
    """
    Singleton service wrapper simulating text embeddings generation.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(EmbeddingService, cls).__new__(cls, *args, **kwargs)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.lock = threading.Lock()
        logger.info("Initializing mock/fallback embedding generator (lightweight mode)...")
        self._initialized = True

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generates a 384-dimensional vector embedding for a given text input.
        Generates a deterministic simulated vector based on the text hash.
        """
        if not text.strip():
            raise EmbeddingGenerationException("Cannot generate embedding for empty text input.")

        with self.lock:
            try:
                # Deterministic random generator based on the text hash so that identical
                # text queries result in identical mock vectors (allowing basic search verification)
                seed = hash(text) & 0xffffffff
                rng = np.random.default_rng(seed)
                embedding = rng.random(384).astype("float32")
                
                # Normalize the mock embedding vector
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                return embedding
            except Exception as e:
                logger.error(f"Failed to generate simulated embedding: {e}")
                raise EmbeddingGenerationException(f"Error during simulated embedding generation: {e}")
