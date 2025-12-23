from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ChatConfidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DiseasePrediction(BaseModel):
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class AudioTranscriptionResult(BaseModel):
    transcript: str
    provider: Literal["bhashini", "whisper", "unavailable"]
    language: Optional[str] = None


class ChatResponse(BaseModel):
    response_text: str
    confidence: ChatConfidence
    citations: list[Any] = Field(default_factory=list)
    escalate: bool
    reason: str
    audio_output_url: str
    escalation_id: Optional[str] = None
