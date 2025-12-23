"""
API v1 package for the Agricultural Advisory System
"""
from fastapi import APIRouter

router = APIRouter()

# Import all route modules to register them with the router
from . import health  # noqa
