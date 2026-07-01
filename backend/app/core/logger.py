import logging
import os
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler

# Thread-local / Async-local context variable for tracing Request IDs
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")

class RequestIdFilter(logging.Filter):
    """
    Appends the request_id context variable to log records.
    """
    def filter(self, record):
        record.request_id = request_id_ctx_var.get()
        return True

def setup_logging():
    # Ensure logs folder exists
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Base formatter including timestamp, log level, request_id context, logger name, and message
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(request_id)s] [%(name)s:%(lineno)d]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Request ID filter to capture context in logging
    req_id_filter = RequestIdFilter()

    # Root Logger Configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []

    # 1. Console Handler (Standard Output)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(req_id_filter)
    root_logger.addHandler(console_handler)

    # 2. Info File Handler (All logs INFO and above)
    info_handler = RotatingFileHandler(
        os.path.join(log_dir, "info.log"),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    info_handler.addFilter(req_id_filter)
    root_logger.addHandler(info_handler)

    # 3. Error File Handler (Only logs ERROR and CRITICAL)
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "error.log"),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(req_id_filter)
    root_logger.addHandler(error_handler)

    # Quiet external library logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger("insightflow")
