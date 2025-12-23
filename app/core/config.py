"""
Application configuration settings using environment variables
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "AI Agricultural Advisory System"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    allowed_origins: str = "*"

    # HTTP client
    http_timeout_seconds: float = 30.0
    http_retries: int = 2

    # Gemini
    gemini_api_key: Optional[str] = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_model: str = "gemini-1.5-flash"

    # Bhashini
    bhashini_base_url: Optional[str] = None
    bhashini_api_key: Optional[str] = None

    # In-memory cache
    chat_cache_ttl_seconds: int = 900

    # Rate limiting (in-memory)
    rate_limit_enabled: bool = True
    rate_limit_window_seconds: int = 60
    rate_limit_requests: int = 60

    # Upload validation
    max_audio_bytes: int = 10 * 1024 * 1024
    max_image_bytes: int = 10 * 1024 * 1024
    allowed_audio_content_types: str = "audio/wav,audio/x-wav,audio/mpeg,audio/mp3,audio/webm,application/octet-stream"
    allowed_image_content_types: str = "image/jpeg,image/png,image/webp"

    # Auth (JWT)
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @computed_field
    @property
    def allowed_origins_list(self) -> List[str]:
        raw = (self.allowed_origins or "").strip()
        if not raw:
            return ["*"]
        if raw == "*":
            return ["*"]
        return [s.strip() for s in raw.split(",") if s.strip()]

    @computed_field
    @property
    def allowed_audio_content_types_list(self) -> List[str]:
        raw = (self.allowed_audio_content_types or "").strip()
        return [s.strip() for s in raw.split(",") if s.strip()]

    @computed_field
    @property
    def allowed_image_content_types_list(self) -> List[str]:
        raw = (self.allowed_image_content_types or "").strip()
        return [s.strip() for s in raw.split(",") if s.strip()]


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching
    """
    return Settings()
