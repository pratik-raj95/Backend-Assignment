import time
import uuid
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.exceptions import InsightFlowException
from app.core.logger import logger, request_id_ctx_var

class TracingAndSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    HTTP Middleware that:
    1. Sets a unique X-Request-ID for distributed tracing.
    2. Limits maximum request body size to prevent DoS attacks.
    3. Logs request path and latency.
    """
    def __init__(self, app, max_content_length: int = 1048576):  # Default 1MB
        super().__init__(app)
        self.max_content_length = max_content_length

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate request ID
        req_id = request.headers.get("X-Request-ID")
        if not req_id:
            req_id = str(uuid.uuid4())
            
        # Set in ContextVar for logging context mapping
        token = request_id_ctx_var.set(req_id)

        # Enforce Request Body Size Limit
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > self.max_content_length:
                    logger.error(f"Payload size exceeded: {length} bytes (Limit: {self.max_content_length})")
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "success": False,
                            "error": {
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Request body size exceeds the allowed limit of {self.max_content_length} bytes.",
                                "details": None
                            }
                        }
                    )
            except ValueError:
                pass

        start_time = time.time()
        try:
            response = await call_next(request)
            
            # Inject trace ID into response headers
            response.headers["X-Request-ID"] = req_id
            
            latency = (time.time() - start_time) * 1000
            logger.info(f"{request.method} {request.url.path} finished in {latency:.2f}ms - Status: {response.status_code}")
            return response
        except Exception as e:
            # Propagate exceptions to exception handlers
            raise e
        finally:
            # Clean up context var token
            request_id_ctx_var.reset(token)

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global catch-all exception handler for application failures.
    Formats errors into a standard JSON payload.
    """
    # 1. Handle custom app exceptions
    if isinstance(exc, InsightFlowException):
        logger.error(f"Application exception [{exc.code}]: {exc.message} - Details: {exc.details}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )

    # 2. Handle FastAPI/Pydantic validation errors
    if isinstance(exc, RequestValidationError):
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters or payload format.",
                    "details": exc.errors()
                }
            }
        )

    # 3. Handle raw unhandled python exceptions
    logger.critical(f"Unhandled critical exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred on the server.",
                "details": str(exc) if request.app.debug else None
            }
        }
    )
