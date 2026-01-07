"""
AI Voice Agent API - Main Application Entry Point.

A FastAPI application for managing AI voice agents for logistics dispatch.
"""
import logging
import logging.handlers
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import agents_router, calls_router
from app.api.routes.pipecat_calls import router as pipecat_router
from app.api.webhooks import retell_router

# Configure logging with file handler
log_dir = os.path.expanduser("~/logs")
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "backend.log")

# Remove existing handlers to prevent duplicate logs
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)
logging.root.addHandler(console_handler)

# File handler with rotation
file_handler = logging.handlers.RotatingFileHandler(
    log_file_path,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logging.root.addHandler(file_handler)

logging.root.setLevel(logging.DEBUG)  # Set root logger to DEBUG to capture all messages

logger = logging.getLogger(__name__)
logger.info(f"Logging to file: {log_file_path}")


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
app.include_router(pipecat_router, prefix="/api")
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
