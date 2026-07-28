from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security-related HTTP headers to every response.

    - X-Content-Type-Options: nosniff     — prevent MIME-type sniffing
    - X-Frame-Options: DENY               — prevent clickjacking
    - X-XSS-Protection: 0                 — disable legacy XSS filter (modern browsers
                                            ignore this; kept for completeness)
    - Referrer-Policy: strict-origin-when-cross-origin
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
