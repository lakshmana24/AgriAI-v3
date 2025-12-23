"""
API package for the Agricultural Advisory System
"""
from fastapi import APIRouter

from app.api.v1.health import router as health_router

# Create main API router
api_router = APIRouter()

# Include versioned routers
api_router.include_router(health_router, tags=["health"])
