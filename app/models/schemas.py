from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import date


class PolygonRequest(BaseModel):
    """Polygon coordinates for Area of Interest"""
    coordinates: List[List[float]] = Field(
        ...,
        description="List of [longitude, latitude] coordinate pairs forming a closed polygon",
        min_length=4,
        example=[[75.7089111013882, 31.37279750147279],
                 [75.7089111013882, 31.371250459643193],
                 [75.71048323497394, 31.371250459643193],
                 [75.71048323497394, 31.37279750147279],
                 [75.7089111013882, 31.37279750147279]]
    )

    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v):
        if len(v) < 4:
            raise ValueError('Polygon must have at least 4 points')
        # Check if first and last points are the same (closed polygon)
        if v[0] != v[-1]:
            raise ValueError('Polygon must be closed (first and last points must be identical)')
        # Validate coordinate pairs
        for coord in v:
            if len(coord) != 2:
                raise ValueError('Each coordinate must be [longitude, latitude]')
            lon, lat = coord
            if not (-180 <= lon <= 180):
                raise ValueError('Longitude must be between -180 and 180')
            if not (-90 <= lat <= 90):
                raise ValueError('Latitude must be between -90 and 90')
        return v


class NDVIRequest(BaseModel):
    """Request model for NDVI analysis"""
    aoi: PolygonRequest = Field(..., description="Area of Interest polygon")
    start_date: date = Field(..., description="Start date for image collection (YYYY-MM-DD)")
    end_date: date = Field(..., description="End date for image collection (YYYY-MM-DD)")
    bands: Optional[List[str]] = Field(
        default=["B4", "B8"],
        description="List of Sentinel-2 bands to include. B4 and B8 are required for NDVI."
    )
    cloud_filter: Optional[int] = Field(
        default=60,
        ge=0,
        le=100,
        description="Maximum percentage of cloudy pixels to include"
    )
    cld_prb_thresh: Optional[int] = Field(
        default=20,
        ge=0,
        le=100,
        description="Cloud probability threshold"
    )
    nir_drk_thresh: Optional[float] = Field(
        default=0.15,
        ge=0,
        le=1,
        description="Threshold for dark NIR pixels"
    )
    cld_prj_dist: Optional[float] = Field(
        default=1.0,
        ge=0,
        description="Distance for projecting cloud shadows"
    )
    buffer: Optional[int] = Field(
        default=50,
        ge=0,
        description="Buffer size for dilating cloud-shadow mask"
    )


class ZonalStatsRequest(NDVIRequest):
    """Request model for Zonal Statistics with NDVI"""
    reducer: Optional[str] = Field(
        default="mean",
        description="Statistical reducer: mean, median, min, max, mode, stdDev, var, sum"
    )
    scale: Optional[int] = Field(
        default=10,
        ge=1,
        description="Scale in meters for zonal statistics calculation"
    )

    @field_validator('reducer')
    @classmethod
    def validate_reducer(cls, v):
        valid_reducers = ['mean', 'median', 'min', 'max', 'mode', 'stdDev', 'var', 'sum']
        if v not in valid_reducers:
            raise ValueError(f'Reducer must be one of: {", ".join(valid_reducers)}')
        return v


class NDVIResponse(BaseModel):
    """Response model for NDVI analysis"""
    status: str = Field(..., description="Status of the request")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="NDVI analysis results"
    )


class ZonalStatsResponse(BaseModel):
    """Response model for Zonal Statistics"""
    status: str = Field(..., description="Status of the request")
    message: str = Field(..., description="Response message")
    records_count: Optional[int] = Field(
        default=None,
        description="Number of records returned"
    )
    data: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Zonal statistics results as list of records"
    )


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    gee_initialized: bool = Field(..., description="Whether Google Earth Engine is initialized")

