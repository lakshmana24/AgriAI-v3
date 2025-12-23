from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass(frozen=True)
class BhashiniClientError(Exception):
    message: str
    status_code: Optional[int] = None


class BhashiniClient:
    """Minimal HTTP client for Bhashini speech-to-text.

    The exact API contract may vary by deployment. This client is intentionally
    simple and expects a transcribe endpoint accepting multipart file upload.
    """

    def __init__(self) -> None:
        self._timeout = httpx.Timeout(settings.http_timeout_seconds)
        self._retries = settings.http_retries
        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            transport=httpx.AsyncHTTPTransport(retries=self._retries),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def transcribe(self, audio_bytes: bytes, filename: str, content_type: str) -> str:
        if not settings.bhashini_base_url:
            raise BhashiniClientError("BHASHINI_BASE_URL is not configured")

        url = f"{settings.bhashini_base_url.rstrip('/')}/transcribe"
        headers = {}
        if settings.bhashini_api_key:
            headers["Authorization"] = f"Bearer {settings.bhashini_api_key}"

        files = {"audio": (filename, audio_bytes, content_type)}

        try:
            resp = await self._client.post(url, files=files, headers=headers)
        except httpx.TimeoutException as exc:
            raise BhashiniClientError("Bhashini request timed out") from exc
        except httpx.RequestError as exc:
            raise BhashiniClientError("Bhashini request failed") from exc

        if resp.status_code >= 400:
            logger.warning(
                "Bhashini error response",
                status_code=resp.status_code,
                body=resp.text[:2000],
            )
            raise BhashiniClientError("Bhashini returned an error", status_code=resp.status_code)

        data = resp.json()
        transcript = data.get("transcript") or data.get("text")
        if not transcript:
            raise BhashiniClientError("Bhashini response missing transcript")
        return str(transcript)


bhashini_client = BhashiniClient()
