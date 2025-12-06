from fastapi import APIRouter, Depends
import logging
import ee
from app.models.schemas import HealthResponse
from app.core.config import settings
from app.core.dependencies import get_ee_initialized

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check(_: bool = Depends(get_ee_initialized)) -> HealthResponse:
    """
    Health check endpoint to verify service status and Google Earth Engine initialization.
    
    **Returns:**
    - Service status
    - API version
    - Google Earth Engine initialization status
    """
    try:
        # Check if GEE is properly initialized by making a simple call
        ee_initialized = False
        try:
            ee.Number(1).getInfo()
            ee_initialized = True
        except Exception:
            pass
        
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            gee_initialized=ee_initialized
        )
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            gee_initialized=False
        )

