"""FastAPI application factory and configuration."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import get_settings
from .routes import health_router, pricing_router, simulation_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Data directory: {settings.data_dir}")
    
    yield
    
    # Shutdown
    print("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
## Movesion Business Model Simulator API

A comprehensive API for simulating and analyzing card program economics.

### Features
- **Scenario Simulation**: Run detailed monthly projections based on user adoption, spending patterns, and fee structures
- **Pricing Plan Management**: Access and configure Wallester pricing tiers and fees
- **Comparison Tools**: Compare multiple scenarios side-by-side
- **Sensitivity Analysis**: Understand how key parameters affect profitability

### Quick Start
1. Fetch available presets: `GET /api/v1/pricing/presets`
2. Run a simulation: `POST /api/v1/simulation/run`
3. Compare scenarios: `POST /api/v1/simulation/compare`
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler for unhandled errors."""
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else None,
                "code": "INTERNAL_ERROR",
            },
        )
    
    # Include routers
    api_prefix = settings.api_prefix
    
    app.include_router(health_router, prefix=api_prefix)
    app.include_router(pricing_router, prefix=api_prefix)
    app.include_router(simulation_router, prefix=api_prefix)
    
    # Also include health at root level
    app.include_router(health_router)
    
    return app


# Create default app instance for uvicorn
app = create_app()
