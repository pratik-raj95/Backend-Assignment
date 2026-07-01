import threading
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import EmbeddingGenerationException

class EmbeddingService:
    """
    Singleton service wrapper around SentenceTransformer to generate text embeddings.
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
        self.model = None
        self.use_fallback = False
        self.lock = threading.Lock()
        
        self._load_model()
        self._initialized = True

    def _load_model(self):
        """
        Loads the SentenceTransformer model into memory.
        If loading fails, configures the service to run in fallback simulation mode.
        """
        with self.lock:
            try:
                logger.info(f"Loading SentenceTransformer model '{self.model_name}'...")
                # Automatically loads model on CPU/GPU as appropriate
                self.model = SentenceTransformer(self.model_name)
                logger.info("Model loaded successfully.")
            except Exception as e:
                logger.warning(
                    f"Failed to load SentenceTransformer model: {e}. "
                    "Falling back to simulated/mock embeddings generator."
                )
                self.use_fallback = True
                self.model = None

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generates a 384-dimensional vector embedding for a given text input.
        If in fallback mode, generates a deterministic simulated vector.
        """
        if not text.strip():
            raise EmbeddingGenerationException("Cannot generate embedding for empty text input.")

        with self.lock:
            if self.use_fallback or self.model is None:
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
                    logger.error(f"Failed to generate simulated fallback embedding: {e}")
                    raise EmbeddingGenerationException(f"Error during fallback embedding generation: {e}")

            try:
                # encode returns a numpy ndarray representing the embedding
                embedding = self.model.encode(text, convert_to_numpy=True)
                return embedding
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
                raise EmbeddingGenerationException(f"Error during embedding inference: {e}")
