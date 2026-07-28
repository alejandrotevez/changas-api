"""Global rate-limiter instance (slowapi).

Defined in its own module to avoid circular imports between main.py and routers.
"""

from fastapi import Request
from slowapi import Limiter


def _get_client_host(request: Request) -> str:
    """Extract client IP, gracefully falling back when client is None (e.g. tests)."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"  # fallback for test clients without a remote address


limiter = Limiter(
    key_func=_get_client_host,
    default_limits=["120/minute"],  # global ceiling for all endpoints
)
