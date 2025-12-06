from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
import ee
from app.models.schemas import (
    NDVIRequest,
    ZonalStatsRequest,
    NDVIResponse,
    ZonalStatsResponse
)
from app.services.ndvi_service import NDVIService
from app.core.dependencies import get_ee_initialized

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ndvi", tags=["NDVI"])


@router.post("/zonal-stats", response_model=ZonalStatsResponse)
async def compute_ndvi_zonal_stats(
    request: ZonalStatsRequest,
    _: bool = Depends(get_ee_initialized)
) -> ZonalStatsResponse:
    """
    Compute zonal statistics for NDVI over an area of interest.
    
    This endpoint:
    1. Creates a Sentinel-2 L2A collection for the specified date range and AOI
    2. Applies cloud filtering and masking
    3. Computes NDVI from B4 and B8 bands
    4. Calculates zonal statistics (mean, median, etc.) for the AOI
    
    **Parameters:**
    - **aoi**: Polygon coordinates defining the area of interest
    - **start_date**: Start date for image collection (YYYY-MM-DD)
    - **end_date**: End date for image collection (YYYY-MM-DD)
    - **bands**: List of Sentinel-2 bands (default: ["B4", "B8"] for NDVI)
    - **cloud_filter**: Maximum cloud percentage (0-100, default: 60)
    - **reducer**: Statistical reducer (mean, median, min, max, mode, stdDev, var, sum)
    - **scale**: Scale in meters for computation (default: 10)
    
    **Returns:**
    - Zonal statistics for each image in the collection with NDVI values
    """
    try:
        logger.info(f"Received zonal stats request for date range: {request.start_date} to {request.end_date}")
        
        result = NDVIService.compute_ndvi_zonal_stats(request)
        
        return ZonalStatsResponse(
            status="success",
            message="Zonal statistics computed successfully",
            records_count=result["count"],
            data=result["records"]
        )
        
    except Exception as e:
        logger.error(f"Error in zonal stats endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute zonal statistics: {str(e)}"
        )


@router.post("/collection-info", response_model=NDVIResponse)
async def get_ndvi_collection_info(
    request: NDVIRequest,
    _: bool = Depends(get_ee_initialized)
) -> NDVIResponse:
    """
    Get information about the NDVI collection without computing statistics.
    
    This endpoint provides metadata about the Sentinel-2 collection that would be used
    for NDVI computation, including the number of images available.
    
    **Parameters:**
    - **aoi**: Polygon coordinates defining the area of interest
    - **start_date**: Start date for image collection (YYYY-MM-DD)
    - **end_date**: End date for image collection (YYYY-MM-DD)
    - **bands**: List of Sentinel-2 bands (default: ["B4", "B8"])
    - **cloud_filter**: Maximum cloud percentage (0-100, default: 60)
    
    **Returns:**
    - Collection metadata including size and date range
    """
    try:
        logger.info(f"Received collection info request for date range: {request.start_date} to {request.end_date}")
        
        result = NDVIService.get_ndvi_collection_info(request)
        
        return NDVIResponse(
            status="success",
            message="Collection information retrieved successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error in collection info endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collection info: {str(e)}"
        )

