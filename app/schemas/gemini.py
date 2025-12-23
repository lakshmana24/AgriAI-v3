from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GeminiConfidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class GeminiStructuredResponse(BaseModel):
    answer: str = Field(..., min_length=1)
    confidence: GeminiConfidence
    citations: list[Any] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    uncertainty: bool
