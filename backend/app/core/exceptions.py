from typing import Any, Optional

class InsightFlowException(Exception):
    """Base exception for InsightFlow AI application errors."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

class EntityNotFoundException(InsightFlowException):
    """Raised when a requested resource is not found in the system."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details
        )

class ValidationException(InsightFlowException):
    """Raised when request payload or data schema validation fails."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class EmbeddingGenerationException(InsightFlowException):
    """Raised when sentence embeddings fail to generate."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="EMBEDDING_FAILURE",
            status_code=502,
            details=details
        )

class VectorSearchException(InsightFlowException):
    """Raised when operations in the FAISS index fail."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VECTOR_SEARCH_ERROR",
            status_code=500,
            details=details
        )
