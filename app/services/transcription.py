from __future__ import annotations

from typing import Optional

from app.core.logging import get_logger
from app.schemas.chat import AudioTranscriptionResult
from app.services.bhashini_client import BhashiniClientError, bhashini_client

logger = get_logger(__name__)


class WhisperTranscriber:
    """Local Whisper fallback.

    Uses `whisper` if installed. If not installed, returns unavailable.
    """

    async def transcribe(self, audio_bytes: bytes) -> AudioTranscriptionResult:
        try:
            import tempfile

            import whisper  # type: ignore
        except Exception:
            return AudioTranscriptionResult(transcript="", provider="unavailable", language=None)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            model = whisper.load_model("base")
            result = model.transcribe(tmp.name)
            text = (result or {}).get("text") or ""
            lang = (result or {}).get("language")
            return AudioTranscriptionResult(transcript=str(text).strip(), provider="whisper", language=lang)


class AudioTranscriptionService:
    def __init__(self) -> None:
        self._whisper = WhisperTranscriber()

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> AudioTranscriptionResult:
        if not audio_bytes:
            return AudioTranscriptionResult(transcript="", provider="unavailable", language=None)

        try:
            transcript = await bhashini_client.transcribe(
                audio_bytes=audio_bytes,
                filename=filename,
                content_type=content_type,
            )
            return AudioTranscriptionResult(transcript=transcript, provider="bhashini", language=None)
        except BhashiniClientError as exc:
            logger.warning("Bhashini unavailable, falling back to Whisper", message=exc.message)
            return await self._whisper.transcribe(audio_bytes)


audio_transcription_service = AudioTranscriptionService()
