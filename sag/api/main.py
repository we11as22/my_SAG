"""SAG API main entry point

FastAPI application entry point, configures routes, middleware, global exception handling
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sag import __version__
from sag.api.middleware import LoggingMiddleware, TimingMiddleware
from sag.api.routers import (
    chat,
    documents,
    entity_types,
    model_configs,
    pipeline,
    sources,
    tasks,
)
from sag.api.schemas.common import ErrorResponse
from sag.core.config.settings import get_settings
from sag.exceptions import SAGError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifecycle management"""
    # Initialize on startup
    print("🚀 SAG API starting...")
    print(f"📦 Version: {__version__}")

    settings = get_settings()
    print(f"🔧 Configuration loaded")
    print(f"   - Database: {settings.mysql_host}:{settings.mysql_port}")
    print(f"   - Elasticsearch: {settings.elasticsearch_url}")
    print(f"   - Redis: {settings.redis_host}:{settings.redis_port}")

    yield

    # Cleanup on shutdown
    print("👋 SAG API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="SAG API",
    description="Data flow intelligent engine based on SQL-RAG theory - provides backend support for Web UI",
    version=__version__,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS configuration
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development environment allows all origins, production needs specific domain configuration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(TimingMiddleware)
app.add_middleware(LoggingMiddleware)


# Global exception handling
@app.exception_handler(SAGError)
async def sag_exception_handler(request: Request, exc: SAGError):
    """SAG business exception handling"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            success=False,
            error={
                "code": exc.__class__.__name__,
                "message": str(exc),
                "details": getattr(exc, "details", None),
            },
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Parameter validation exception handling"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            success=False,
            error={
                "code": "VALIDATION_ERROR",
                "message": "Request parameter validation failed",
                "details": exc.errors(),
            },
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handling"""
    print(f"❌ Unhandled exception: {exc}")
    import traceback

    traceback.print_exc()

    # Get configuration to decide whether to show detailed errors
    try:
        settings = get_settings()
        show_details = getattr(settings, "debug", False)
    except:
        show_details = False

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            error={
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": str(exc) if show_details else None,
            },
        ).model_dump(),
    )


# Register routes
app.include_router(sources.router, prefix="/api/v1", tags=["Source Management"])
app.include_router(entity_types.router, prefix="/api/v1", tags=["Entity Type Management"])
app.include_router(documents.router, prefix="/api/v1", tags=["Document Management"])
app.include_router(pipeline.router, prefix="/api/v1", tags=["Unified Pipeline"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Task Management"])
app.include_router(chat.router, prefix="/api/v1", tags=["AI Chat"])
# Model configuration routes
app.include_router(model_configs.router, prefix="/api/v1/model-configs", tags=["Model Configuration"])


# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "version": __version__,
        "service": "SAG API",
    }


# Home page
@app.get("/", tags=["System"])
async def root():
    """API home page"""
    return {
        "service": "SAG API",
        "version": __version__,
        "description": "Data flow intelligent engine based on SQL-RAG theory",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "health": "/health",
        "features": {
            "source_management": "Source configuration management",
            "custom_entity_types": "Custom entity dimensions",
            "document_upload": "Document upload processing",
            "load_extract_search": "Load-Extract-Search pipeline",
            "flexible_combination": "Flexible combination, can be separated or combined",
        },
    }


if __name__ == "__main__":
    import os
    import uvicorn

    # Read configuration from environment variables
    workers = int(os.getenv("API_WORKERS", "1"))
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    print(f"🔧 Uvicorn configuration:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Workers: {workers}")
    
    if workers > 1:
        # Multi-worker mode (production environment - Linux server)
        print(f"🚀 Starting production mode ({workers} workers)...")
        uvicorn.run(
            "sag.api.main:app",
            host=host,
            port=port,
            workers=workers,
            log_level="info",
        )
    else:
        # Single worker mode (development environment - local/macOS)
        print(f"🚀 Starting development mode (single worker, hot reload)...")
        uvicorn.run(
            "sag.api.main:app",
            host=host,
            port=port,
            reload=True,  # Development mode supports hot reload
            log_level="info",
        )

