"""Health check routes."""

from fastapi import APIRouter

from ..schemas import HealthResponse
from ...config import get_settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the API is running and healthy.",
)
async def health_check() -> HealthResponse:
    """Return health status of the API."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        service=settings.app_name,
    )


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Root Endpoint",
    description="Root endpoint returning API info.",
)
async def root() -> HealthResponse:
    """Return API info at root endpoint."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        service=settings.app_name,
    )
