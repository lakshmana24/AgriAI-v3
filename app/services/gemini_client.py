from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.prompts.gemini import build_gemini_prompt
from app.schemas.gemini import GeminiStructuredResponse

logger = get_logger(__name__)
settings = get_settings()


@dataclass(frozen=True)
class GeminiClientError(Exception):
    message: str
    status_code: Optional[int] = None


class GeminiClient:
    """Portable Gemini HTTP client (no SDK assumptions)."""

    def __init__(self) -> None:
        self._timeout = httpx.Timeout(settings.http_timeout_seconds)
        self._retries = settings.http_retries

        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            transport=httpx.AsyncHTTPTransport(retries=self._retries),
            headers={"Content-Type": "application/json"},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def generate_structured(self, context: Dict[str, Any]) -> GeminiStructuredResponse:
        api_key = settings.gemini_api_key
        if not api_key:
            raise GeminiClientError("GEMINI_API_KEY is not configured")

        prompt = build_gemini_prompt(context)

        url = (
            f"{settings.gemini_base_url}/models/{settings.gemini_model}:generateContent"
            f"?key={api_key}"
        )

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 1024,
            },
        }

        try:
            resp = await self._client.post(url, json=payload)
        except httpx.TimeoutException as exc:
            raise GeminiClientError("Gemini request timed out") from exc
        except httpx.RequestError as exc:
            raise GeminiClientError("Gemini request failed") from exc

        if resp.status_code >= 400:
            logger.warning(
                "Gemini error response",
                status_code=resp.status_code,
                body=resp.text[:2000],
            )
            raise GeminiClientError("Gemini returned an error", status_code=resp.status_code)

        try:
            data = resp.json()
        except ValueError as exc:
            raise GeminiClientError("Gemini returned non-JSON response") from exc

        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        parsed = self._parse_strict_json(text)
        try:
            return GeminiStructuredResponse.model_validate(parsed)
        except Exception as exc:
            logger.warning("Gemini response schema validation failed", raw=text[:2000])
            raise GeminiClientError("Gemini response did not match required schema") from exc

    def _parse_strict_json(self, text: str) -> Dict[str, Any]:
        raw = text.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise GeminiClientError("Gemini response was not JSON")
            return json.loads(match.group(0))


gemini_client = GeminiClient()
