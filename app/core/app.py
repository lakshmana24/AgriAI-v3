"""
FastAPI application factory and middleware
"""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import api_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.officer import router as officer_router
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.logging import setup_logging
from app.middleware.rate_limit import InMemoryRateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.schemas.errors import ErrorBody, ErrorResponse

logger = get_logger(__name__)
settings = get_settings()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(InMemoryRateLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)

    # Canonical versioned API
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(officer_router, prefix="/api/v1")

    # Backward-compatible aliases (legacy /chat, /auth, /officer)
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(officer_router)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        payload = ErrorResponse(
            error=ErrorBody(
                code="HTTP_ERROR",
                message=str(exc.detail) if exc.detail else "Request failed",
                details=None,
                request_id=request_id,
            )
        ).model_dump()
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.error("Validation error", path=request.url.path, errors=exc.errors(), request_id=request_id)
        payload = ErrorResponse(
            error=ErrorBody(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"errors": exc.errors()},
                request_id=request_id,
            )
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled exception", exc_info=exc, request_id=request_id)
        payload = ErrorResponse(
            error=ErrorBody(
                code="INTERNAL_ERROR",
                message="Internal server error",
                details=None,
                request_id=request_id,
            )
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)

    # Add startup and shutdown event handlers
    @app.on_event("startup")
    async def startup_event() -> None:
        setup_logging()
        logger.info("Application startup")

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        logger.info("Application shutdown")

    return app


# Create the application instance
app = create_application()
