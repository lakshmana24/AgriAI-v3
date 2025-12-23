from __future__ import annotations

import time
from dataclasses import dataclass
from threading import RLock
from typing import Dict, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.schemas.errors import ErrorBody, ErrorResponse

settings = get_settings()


@dataclass
class _Window:
    start: float
    count: int


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._lock = RLock()
        self._windows: Dict[Tuple[str, str], _Window] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        route_key = request.url.path
        key = (ip, route_key)

        now = time.monotonic()
        window = settings.rate_limit_window_seconds
        limit = settings.rate_limit_requests

        with self._lock:
            current = self._windows.get(key)
            if current is None or (now - current.start) >= window:
                self._windows[key] = _Window(start=now, count=1)
            else:
                current.count += 1
                if current.count > limit:
                    request_id = getattr(request.state, "request_id", None)
                    payload = ErrorResponse(
                        error=ErrorBody(
                            code="RATE_LIMITED",
                            message="Too many requests",
                            details={"limit": limit, "window_seconds": window},
                            request_id=request_id,
                        )
                    ).model_dump()
                    return JSONResponse(status_code=429, content=payload)

        return await call_next(request)
