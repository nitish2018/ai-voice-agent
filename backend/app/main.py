"""
AI Voice Agent API - Main Application Entry Point.

A FastAPI application for managing AI voice agents for logistics dispatch.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import agents_router, calls_router
from app.api.webhooks import retell_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    yield
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Dispatcher Voice Agent Administration Platform API.
    
    This API provides endpoints for:
    - Configuring voice agent prompts and settings
    - Triggering test calls to drivers
    - Viewing call results and transcripts
    - Receiving webhooks from Retell AI
    
    ## Features
    
    ### Agent Configuration
    Create and manage voice agents with custom prompts, voice settings,
    and emergency protocols.
    
    ### Call Management
    Trigger outbound calls to drivers with context (name, load number)
    and view structured results extracted from transcripts.
    
    ### Logistics Scenarios
    - **Driver Check-in**: Status updates, ETA, arrival confirmation
    - **Emergency Protocol**: Dynamic escalation handling
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router, prefix="/api")
app.include_router(calls_router, prefix="/api")
app.include_router(retell_router)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
    }


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
