from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.chat import ChatResponse
from app.services.multimodal_chat import multimodal_chat_service

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    text: Optional[str] = Form(default=None),
    audio: Optional[UploadFile] = File(default=None),
    image: Optional[UploadFile] = File(default=None),
) -> ChatResponse:
    if text is None and audio is None and image is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one of text, audio, or image must be provided.",
        )

    audio_bytes = None
    audio_filename = None
    audio_content_type = None
    if audio is not None:
        if audio.content_type and audio.content_type not in settings.allowed_audio_content_types_list:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported audio content type.",
            )
        audio_bytes = await audio.read()
        if len(audio_bytes) > settings.max_audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Audio file too large.",
            )
        audio_filename = audio.filename or "audio"
        audio_content_type = audio.content_type or "application/octet-stream"

    image_bytes = None
    image_filename = None
    if image is not None:
        if image.content_type and image.content_type not in settings.allowed_image_content_types_list:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported image content type.",
            )
        image_bytes = await image.read()
        if len(image_bytes) > settings.max_image_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image file too large.",
            )
        image_filename = image.filename or "image"

    logger.info(
        "Chat request received",
        has_text=bool(text),
        has_audio=audio is not None,
        has_image=image is not None,
    )

    return await multimodal_chat_service.chat(
        text=text,
        audio_bytes=audio_bytes,
        audio_filename=audio_filename,
        audio_content_type=audio_content_type,
        image_bytes=image_bytes,
        image_filename=image_filename,
    )
