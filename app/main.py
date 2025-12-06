from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from app.routers import ndvi, health
from app.core.dependencies import get_ee_initialized

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="NDVI Analysis Microservice using Google Earth Engine and Sentinel-2 data",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize Google Earth Engine on startup"""
    logger.info("Starting NDVI Service...")
    try:
        get_ee_initialized()
        logger.info("Google Earth Engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Google Earth Engine: {str(e)}")
        logger.warning("Service will start but GEE operations may fail")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down NDVI Service...")


# Include routers
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(ndvi.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health"
    }

