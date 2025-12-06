"""
Unit tests for NDVI service methods
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from app.services.ndvi_service import NDVIService
from app.models.schemas import NDVIRequest, ZonalStatsRequest, PolygonRequest


class TestNDVIService:
    """Tests for NDVIService class"""
    
    def test_create_aoi_geometry(self, sample_polygon_coordinates):
        """Test creating AOI geometry from coordinates"""
        with patch('app.services.ndvi_service.ee') as mock_ee:
            mock_geometry = MagicMock()
            mock_ee.Geometry.Polygon.return_value = mock_geometry
            
            result = NDVIService.create_aoi_geometry(sample_polygon_coordinates)
            
            mock_ee.Geometry.Polygon.assert_called_once_with([sample_polygon_coordinates])
            assert result == mock_geometry
    
    def test_add_ndvi_band(self):
        """Test adding NDVI band to image"""
        with patch('app.services.ndvi_service.ee') as mock_ee:
            mock_image = MagicMock()
            mock_ndvi = MagicMock()
            mock_image.normalizedDifference.return_value = mock_ndvi
            mock_ndvi.rename.return_value = mock_ndvi
            mock_image.addBands.return_value = mock_image
            
            result = NDVIService.add_ndvi_band(mock_image)
            
            mock_image.normalizedDifference.assert_called_once_with(['B8', 'B4'])
            mock_ndvi.rename.assert_called_once_with('NDVI')
            mock_image.addBands.assert_called_once_with(mock_ndvi)
            assert result == mock_image
    
    @patch('app.services.ndvi_service.S2L2ACollection')
    @patch('app.services.ndvi_service.ZonalStats')
    def test_compute_ndvi_zonal_stats_success(
        self, 
        mock_zonal_stats_class,
        mock_s2_collection_class,
        sample_zonal_stats_request
    ):
        """Test successful zonal stats computation"""
        import pandas as pd
        
        # Mock S2 collection
        mock_s2_col = MagicMock()
        mock_s2_col.col = MagicMock()
        mock_s2_collection_class.return_value = mock_s2_col
        
        # Mock image collection with map
        mock_image_col = MagicMock()
        mock_s2_col.col.map.return_value = mock_image_col
        
        # Mock zonal stats
        mock_zonal_stats = MagicMock()
        mock_zonal_stats_class.return_value = mock_zonal_stats
        
        # Mock DataFrame result
        mock_df = pd.DataFrame({
            'imageID': ['img1', 'img2'],
            'Date': ['01-01-2020', '02-01-2020'],
            'NDVI': [0.65, 0.72]
        })
        mock_zonal_stats.execute.return_value = mock_df
        
        # Mock EE objects
        with patch('app.services.ndvi_service.ee') as mock_ee:
            mock_ee.Geometry.Polygon.return_value = MagicMock()
            mock_ee.FeatureCollection.return_value = MagicMock()
            mock_ee.Feature.return_value = MagicMock()
            
            result = NDVIService.compute_ndvi_zonal_stats(sample_zonal_stats_request)
            
            assert result["count"] == 2
            assert len(result["records"]) == 2
            assert "columns" in result
            assert result["records"][0]["NDVI"] == 0.65
    
    @patch('app.services.ndvi_service.S2L2ACollection')
    def test_compute_ndvi_zonal_stats_exception(
        self,
        mock_s2_collection_class,
        sample_zonal_stats_request
    ):
        """Test exception handling in zonal stats computation"""
        # Mock S2 collection to raise exception
        mock_s2_collection_class.side_effect = Exception("Collection creation failed")
        
        with patch('app.services.ndvi_service.ee') as mock_ee:
            mock_ee.Geometry.Polygon.return_value = MagicMock()
            
            with pytest.raises(Exception) as exc_info:
                NDVIService.compute_ndvi_zonal_stats(sample_zonal_stats_request)
            
            assert "Failed to compute zonal statistics" in str(exc_info.value)
    
    @patch('app.services.ndvi_service.S2L2ACollection')
    def test_get_ndvi_collection_info_success(
        self,
        mock_s2_collection_class,
        sample_ndvi_request
    ):
        """Test successful collection info retrieval"""
        # Mock S2 collection
        mock_s2_col = MagicMock()
        mock_s2_col.col = MagicMock()
        mock_s2_col.col.size.return_value = MagicMock()
        mock_s2_col.col.size.return_value.getInfo.return_value = 10
        mock_s2_collection_class.return_value = mock_s2_col
        
        with patch('app.services.ndvi_service.ee') as mock_ee:
            mock_ee.Geometry.Polygon.return_value = MagicMock()
            
            result = NDVIService.get_ndvi_collection_info(sample_ndvi_request)
            
            assert result["collection_size"] == 10
            assert result["date_range"]["start"] == "2020-01-01"
            assert result["date_range"]["end"] == "2020-01-31"
            assert result["bands"] == ["B4", "B8"]
            assert "aoi_coordinates" in result
    
    @patch('app.services.ndvi_service.S2L2ACollection')
    def test_get_ndvi_collection_info_exception(
        self,
        mock_s2_collection_class,
        sample_ndvi_request
    ):
        """Test exception handling in collection info retrieval"""
        # Mock S2 collection to raise exception
        mock_s2_collection_class.side_effect = Exception("Collection creation failed")
        
        with patch('app.services.ndvi_service.ee') as mock_ee:
            mock_ee.Geometry.Polygon.return_value = MagicMock()
            
            with pytest.raises(Exception) as exc_info:
                NDVIService.get_ndvi_collection_info(sample_ndvi_request)
            
            assert "Failed to get collection info" in str(exc_info.value)

