from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, List, Optional

from app.schemas.chat import ChatConfidence, ChatResponse
from app.schemas.officer import EscalationRecord
from app.utils.ttl_cache import TTLCache
from app.core.config import get_settings

settings = get_settings()


@dataclass(frozen=True)
class EscalationNotFound(Exception):
    escalation_id: str


class EscalationStore:
    """In-memory escalation store for officer review."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._cache: TTLCache[str, Dict[str, Any]] = TTLCache(
            ttl_seconds=float(settings.chat_cache_ttl_seconds),
            max_items=1000,
        )

    def add(self, escalation_id: str, context: Dict[str, Any], ai_response: ChatResponse) -> None:
        with self._lock:
            self._cache.set(
                escalation_id,
                {
                    "id": escalation_id,
                    "created_at": datetime.now(timezone.utc),
                    "context": context,
                    "ai_response": ai_response,
                    "verified_response": None,
                },
            )

    def list_all(self) -> List[EscalationRecord]:
        with self._lock:
            items = list(self._cache.items().values())
        records: List[EscalationRecord] = []
        for it in items:
            records.append(
                EscalationRecord(
                    id=it["id"],
                    created_at=it["created_at"],
                    context=it["context"],
                    ai_response=it["ai_response"],
                    verified_response=it.get("verified_response"),
                )
            )
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records

    def get(self, escalation_id: str) -> EscalationRecord:
        item = self._cache.get(escalation_id)
        if not item:
            raise EscalationNotFound(escalation_id)
        return EscalationRecord(
            id=item["id"],
            created_at=item["created_at"],
            context=item["context"],
            ai_response=item["ai_response"],
            verified_response=item.get("verified_response"),
        )

    def respond(self, escalation_id: str, response_text: str, citations: list[Any]) -> EscalationRecord:
        item = self._cache.get(escalation_id)
        if not item:
            raise EscalationNotFound(escalation_id)

        original_ai = item.get("ai_response")
        verified = ChatResponse(
            response_text=response_text,
            confidence=ChatConfidence.HIGH,
            citations=citations,
            escalate=False,
            reason="Verified by officer",
            audio_output_url="",
        )

        if isinstance(item.get("context"), dict) and original_ai is not None:
            item["context"]["ai_response_original"] = getattr(original_ai, "model_dump", lambda: original_ai)()

        item["ai_response"] = verified
        item["verified_response"] = verified
        self._cache.set(escalation_id, item)
        return self.get(escalation_id)


escalation_store = EscalationStore()
