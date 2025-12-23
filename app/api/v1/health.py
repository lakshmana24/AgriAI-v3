"""
Health check endpoints
"""
from datetime import datetime
from typing import Dict, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["health"])


class HealthCheckResponse(BaseModel):
    status: Literal["ok", "error"]
    version: str
    timestamp: datetime
    service: str


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint
    
    Returns:
        Dict: Application health status and metadata
    """
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "version": settings.app_version,
        "timestamp": datetime.utcnow(),
        "service": settings.app_name,
    }
