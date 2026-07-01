from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared SlowAPI limiter using client remote IP address
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"]  # System baseline fallback
)
