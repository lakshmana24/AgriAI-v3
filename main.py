from __future__ import annotations

import uvicorn

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.app import app

settings = get_settings()


def main() -> None:
    setup_logging()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
