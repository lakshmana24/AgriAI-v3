from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorBody
