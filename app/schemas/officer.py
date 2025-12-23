from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.chat import ChatResponse


class EscalationRecord(BaseModel):
    id: str
    created_at: datetime
    context: dict[str, Any]
    ai_response: ChatResponse
    verified_response: Optional[ChatResponse] = None


class OfficerVerifiedAdviceRequest(BaseModel):
    response_text: str = Field(..., min_length=1)
    citations: list[Any] = Field(default_factory=list)
