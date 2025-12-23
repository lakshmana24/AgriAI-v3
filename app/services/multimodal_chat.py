from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.chat import ChatConfidence, ChatResponse
from app.services.escalation_store import EscalationNotFound, escalation_store
from app.services.gemini_client import GeminiClientError, gemini_client
from app.services.image_detection import crop_disease_detector
from app.services.text_processing import text_processor
from app.services.transcription import audio_transcription_service
from app.utils.ttl_cache import TTLCache

logger = get_logger(__name__)
settings = get_settings()


class MultimodalChatService:
    def __init__(self) -> None:
        self._cache: TTLCache[str, Dict[str, Any]] = TTLCache(
            ttl_seconds=float(settings.chat_cache_ttl_seconds),
            max_items=1000,
        )

    async def chat(
        self,
        text: Optional[str],
        audio_bytes: Optional[bytes],
        audio_filename: Optional[str],
        audio_content_type: Optional[str],
        image_bytes: Optional[bytes],
        image_filename: Optional[str],
    ) -> ChatResponse:
        text_signals = text_processor.process(text)

        transcription = None
        if audio_bytes is not None and audio_filename and audio_content_type:
            transcription = await audio_transcription_service.transcribe(
                audio_bytes=audio_bytes,
                filename=audio_filename,
                content_type=audio_content_type,
            )

        predictions = []
        if image_bytes is not None and image_filename:
            predictions = await crop_disease_detector.detect(image_bytes=image_bytes, filename=image_filename)

        context: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inputs": {
                "text": (text_signals.normalized_text if text_signals else None),
                "text_language": (text_signals.language if text_signals else None),
                "audio_transcript": (transcription.transcript if transcription else None),
                "audio_provider": (transcription.provider if transcription else None),
                "audio_language": (transcription.language if transcription else None),
                "image_filename": image_filename,
                "image_predictions": [p.model_dump() for p in predictions],
            },
        }

        try:
            gemini_resp = await gemini_client.generate_structured(context=context)
            confidence = ChatConfidence(gemini_resp.confidence.value)
            escalate, reason = self._escalation(confidence=confidence, uncertainty=gemini_resp.uncertainty)
            response = ChatResponse(
                response_text=gemini_resp.answer,
                confidence=confidence,
                citations=gemini_resp.citations,
                escalate=escalate,
                reason=reason,
                audio_output_url="",
            )
        except GeminiClientError as exc:
            logger.warning("Gemini unavailable", message=exc.message, status_code=exc.status_code)
            response = ChatResponse(
                response_text=(
                    "I can't generate a reliable advisory response right now. "
                    "Please try again shortly or contact an agriculture officer."
                ),
                confidence=ChatConfidence.LOW,
                citations=[],
                escalate=True,
                reason="AI reasoning service is unavailable or returned an invalid response.",
                audio_output_url="",
            )

        escalation_id = None
        if response.escalate:
            escalation_id = str(uuid.uuid4())
            escalation_store.add(
                escalation_id=escalation_id,
                context=context,
                ai_response=response,
            )
            response.escalation_id = escalation_id

            try:
                record = escalation_store.get(escalation_id)
                if record.verified_response is not None:
                    return record.verified_response
            except EscalationNotFound:
                pass

        request_id = str(uuid.uuid4())
        self._cache.set(
            request_id,
            {
                "request": context,
                "response": response.model_dump(),
            },
        )
        return response

    def _escalation(self, confidence: ChatConfidence, uncertainty: bool) -> tuple[bool, str]:
        if confidence == ChatConfidence.LOW:
            return True, "AI confidence is Low; escalate to a human expert."
        if uncertainty:
            return True, "Model indicated uncertainty; escalate to a human expert."
        return False, ""


multimodal_chat_service = MultimodalChatService()
