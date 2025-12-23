from __future__ import annotations

import time
import uuid
from typing import Callable

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response: Response | None = None
        try:
            response = await call_next(request)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            client = request.client.host if request.client else None
            status_code = getattr(response, "status_code", None)
            logger.info(
                "request",
                method=request.method,
                path=str(request.url.path),
                status_code=status_code,
                client_ip=client,
                duration_ms=round(duration_ms, 2),
                request_id=request_id,
            )
            structlog.contextvars.clear_contextvars()

        if response is not None:
            response.headers["x-request-id"] = request_id
            return response
        raise RuntimeError("Request processing failed before a response was created")
