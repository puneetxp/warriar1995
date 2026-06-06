"""
middleware/request_logger.py

Logs every request with method, path, status code, and latency.
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from security.logger import get_logger

logger = get_logger("http")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": elapsed_ms,
                "client": request.client.host if request.client else "unknown",
            },
        )
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
        return response
