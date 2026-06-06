"""
middleware/rate_limiter.py

Sliding-window rate limiter middleware.
Limits requests per client IP to prevent abuse of LLM endpoints.
"""

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from security.logger import get_logger

logger = get_logger("rate_limiter")

# IP → deque of request timestamps
_WINDOWS: Dict[str, Deque[float]] = defaultdict(deque)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter.

    Allows RATE_LIMIT_CALLS requests per RATE_LIMIT_PERIOD seconds per IP.
    Health check and docs endpoints are exempt.
    """

    EXEMPT_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app, calls: int = 30, period: int = 60) -> None:
        super().__init__(app)
        self.calls = calls
        self.period = period

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = _WINDOWS[client_ip]

        # Evict timestamps outside the sliding window
        cutoff = now - self.period
        while window and window[0] < cutoff:
            window.popleft()

        if len(window) >= self.calls:
            retry_after = int(self.period - (now - window[0])) + 1
            logger.warning(
                "Rate limit exceeded",
                extra={"client_ip": client_ip, "path": request.url.path},
            )
            from models.errors import ErrorResponse
            from utils.i18n import get_locale, t
            
            locale = get_locale(request)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    **ErrorResponse(
                        error_code="rate_limit_exceeded",
                        message=t("error.rate_limit", locale, seconds=str(retry_after)),
                        detail=f"Rate limit exceeded: {self.calls} requests allowed per {self.period} seconds.",
                        suggestion=t("error.rate_limit_suggestion", locale),
                        help_url="/docs",
                    ).model_dump(),
                    "error": "rate_limit_exceeded",
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "Content-Language": locale,
                },
            )

        window.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(self.calls - len(window))
        return response
