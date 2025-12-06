import ee
import logging
from typing import Dict, Any, List
from datetime import date
from GeoKit.raster_classes.S2L2ACollection import S2L2ACollection
from GeoKit.raster_analysis.ZonalStats import ZonalStats
from app.models.schemas import NDVIRequest, ZonalStatsRequest

logger = logging.getLogger(__name__)


class NDVIService:
    """Service for NDVI analysis operations"""

    @staticmethod
    def create_aoi_geometry(coordinates: List[List[float]]) -> ee.Geometry:
        """Create Earth Engine Geometry from coordinates"""
        return ee.Geometry.Polygon([coordinates])

    @staticmethod
    def add_ndvi_band(image: ee.Image) -> ee.Image:
        """Add NDVI band to an image"""
        # normalizedDifference is robust to band scale factors (it cancels multiplicative scale)
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return image.addBands(ndvi)

    @staticmethod
    def compute_ndvi_zonal_stats(request: ZonalStatsRequest) -> Dict[str, Any]:
        """
        Compute zonal statistics for NDVI over an area of interest
        
        Args:
            request: ZonalStatsRequest containing all parameters
            
        Returns:
            Dictionary containing the results
        """
        try:
            # Create AOI geometry
            aoi = NDVIService.create_aoi_geometry(request.aoi.coordinates)
            
            # Create Sentinel-2 collection
            logger.info(f"Creating S2 collection from {request.start_date} to {request.end_date}")
            s2_col = S2L2ACollection(
                start=str(request.start_date),
                end=str(request.end_date),
                aoi=aoi,
                bands=request.bands,
                cloud_filter=request.cloud_filter,
                cld_prb_thresh=request.cld_prb_thresh,
                nir_drk_thresh=request.nir_drk_thresh,
                cld_prj_dist=request.cld_prj_dist,
                buffer=request.buffer
            )
            
            # Add NDVI band to collection
            logger.info("Adding NDVI band to collection")
            s2_with_ndvi = s2_col.col.map(NDVIService.add_ndvi_band)
            
            # Create feature collection for AOI
            aoi_fc = ee.FeatureCollection([ee.Feature(aoi)])
            
            # Compute zonal statistics
            logger.info(f"Computing zonal statistics with {request.reducer} reducer")
            zonal_stats = ZonalStats(
                img_col=s2_with_ndvi,
                fc=aoi_fc,
                bands=['NDVI'],
                reducer=request.reducer,
                scale=request.scale
            )
            
            # Execute and get results
            logger.info("Executing zonal statistics computation")
            df = zonal_stats.execute()
            
            # Convert DataFrame to list of dictionaries
            # Drop geometry column if present for JSON serialization
            if 'geometry' in df.columns:
                df = df.drop(columns=['geometry'])
            
            records = df.to_dict('records')
            
            logger.info(f"Successfully computed zonal statistics: {len(records)} records")
            
            return {
                "records": records,
                "count": len(records),
                "columns": list(df.columns)
            }
            
        except Exception as e:
            logger.error(f"Error computing zonal statistics: {str(e)}", exc_info=True)
            raise Exception(f"Failed to compute zonal statistics: {str(e)}")

    @staticmethod
    def get_ndvi_collection_info(request: NDVIRequest) -> Dict[str, Any]:
        """
        Get information about NDVI collection without computing statistics
        
        Args:
            request: NDVIRequest containing all parameters
            
        Returns:
            Dictionary containing collection information
        """
        try:
            # Create AOI geometry
            aoi = NDVIService.create_aoi_geometry(request.aoi.coordinates)
            
            # Create Sentinel-2 collection
            logger.info(f"Creating S2 collection from {request.start_date} to {request.end_date}")
            s2_col = S2L2ACollection(
                start=str(request.start_date),
                end=str(request.end_date),
                aoi=aoi,
                bands=request.bands,
                cloud_filter=request.cloud_filter,
                cld_prb_thresh=request.cld_prb_thresh,
                nir_drk_thresh=request.nir_drk_thresh,
                cld_prj_dist=request.cld_prj_dist,
                buffer=request.buffer
            )
            
            # Get collection size
            collection_size = s2_col.col.size().getInfo()
            
            logger.info(f"Collection contains {collection_size} images")
            
            return {
                "collection_size": collection_size,
                "date_range": {
                    "start": str(request.start_date),
                    "end": str(request.end_date)
                },
                "bands": request.bands,
                "aoi_coordinates": request.aoi.coordinates
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get collection info: {str(e)}")

