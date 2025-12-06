"""
Unit tests for Pydantic models/schemas
"""
import pytest
from datetime import date
from pydantic import ValidationError
from app.models.schemas import (
    PolygonRequest,
    NDVIRequest,
    ZonalStatsRequest,
    HealthResponse,
    NDVIResponse,
    ZonalStatsResponse
)


class TestPolygonRequest:
    """Tests for PolygonRequest model"""
    
    def test_valid_polygon(self):
        """Test valid polygon coordinates"""
        coords = [
            [75.7089111013882, 31.37279750147279],
            [75.7089111013882, 31.371250459643193],
            [75.71048323497394, 31.371250459643193],
            [75.71048323497394, 31.37279750147279],
            [75.7089111013882, 31.37279750147279]  # Closed
        ]
        polygon = PolygonRequest(coordinates=coords)
        assert len(polygon.coordinates) == 5
        assert polygon.coordinates[0] == polygon.coordinates[-1]
    
    def test_polygon_not_closed(self):
        """Test that polygon must be closed"""
        coords = [
            [75.7089111013882, 31.37279750147279],
            [75.7089111013882, 31.371250459643193],
            [75.71048323497394, 31.371250459643193],
            [75.71048323497394, 31.37279750147279]
        ]
        with pytest.raises(ValidationError) as exc_info:
            PolygonRequest(coordinates=coords)
        assert "must be closed" in str(exc_info.value).lower()
    
    def test_polygon_too_few_points(self):
        """Test that polygon must have at least 4 points"""
        coords = [
            [75.7089111013882, 31.37279750147279],
            [75.7089111013882, 31.371250459643193],
            [75.7089111013882, 31.37279750147279]  # Closed but only 3 points
        ]
        with pytest.raises(ValidationError):
            PolygonRequest(coordinates=coords)
    
    def test_invalid_longitude(self):
        """Test longitude validation"""
        coords = [
            [200.0, 31.37279750147279],  # Invalid longitude
            [75.7089111013882, 31.371250459643193],
            [75.71048323497394, 31.371250459643193],
            [75.71048323497394, 31.37279750147279],
            [200.0, 31.37279750147279]
        ]
        with pytest.raises(ValidationError) as exc_info:
            PolygonRequest(coordinates=coords)
        assert "longitude" in str(exc_info.value).lower()
    
    def test_invalid_latitude(self):
        """Test latitude validation"""
        coords = [
            [75.7089111013882, 100.0],  # Invalid latitude
            [75.7089111013882, 31.371250459643193],
            [75.71048323497394, 31.371250459643193],
            [75.71048323497394, 31.37279750147279],
            [75.7089111013882, 100.0]
        ]
        with pytest.raises(ValidationError) as exc_info:
            PolygonRequest(coordinates=coords)
        assert "latitude" in str(exc_info.value).lower()
    
    def test_invalid_coordinate_format(self):
        """Test that coordinates must be [lon, lat] pairs"""
        coords = [
            [75.7089111013882],  # Missing latitude
            [75.7089111013882, 31.371250459643193],
            [75.71048323497394, 31.371250459643193],
            [75.7089111013882]
        ]
        with pytest.raises(ValidationError):
            PolygonRequest(coordinates=coords)


class TestNDVIRequest:
    """Tests for NDVIRequest model"""
    
    def test_valid_request(self, sample_polygon_coordinates):
        """Test valid NDVI request"""
        from app.models.schemas import PolygonRequest
        
        request = NDVIRequest(
            aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 31)
        )
        assert request.start_date == date(2020, 1, 1)
        assert request.end_date == date(2020, 1, 31)
        assert request.bands == ["B4", "B8"]  # Default
        assert request.cloud_filter == 60  # Default
    
    def test_custom_bands(self, sample_polygon_coordinates):
        """Test custom bands"""
        from app.models.schemas import PolygonRequest
        
        request = NDVIRequest(
            aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 31),
            bands=["B4", "B8", "B2"]
        )
        assert len(request.bands) == 3
        assert "B2" in request.bands
    
    def test_cloud_filter_validation(self, sample_polygon_coordinates):
        """Test cloud filter range validation"""
        from app.models.schemas import PolygonRequest
        
        # Valid range
        request = NDVIRequest(
            aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 31),
            cloud_filter=50
        )
        assert request.cloud_filter == 50
        
        # Invalid: negative
        with pytest.raises(ValidationError):
            NDVIRequest(
                aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
                start_date=date(2020, 1, 1),
                end_date=date(2020, 1, 31),
                cloud_filter=-1
            )
        
        # Invalid: > 100
        with pytest.raises(ValidationError):
            NDVIRequest(
                aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
                start_date=date(2020, 1, 1),
                end_date=date(2020, 1, 31),
                cloud_filter=101
            )


class TestZonalStatsRequest:
    """Tests for ZonalStatsRequest model"""
    
    def test_valid_request(self, sample_polygon_coordinates):
        """Test valid zonal stats request"""
        from app.models.schemas import PolygonRequest
        
        request = ZonalStatsRequest(
            aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 31),
            reducer="mean",
            scale=10
        )
        assert request.reducer == "mean"
        assert request.scale == 10
    
    def test_invalid_reducer(self, sample_polygon_coordinates):
        """Test reducer validation"""
        from app.models.schemas import PolygonRequest
        
        with pytest.raises(ValidationError) as exc_info:
            ZonalStatsRequest(
                aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
                start_date=date(2020, 1, 1),
                end_date=date(2020, 1, 31),
                reducer="invalid_reducer"
            )
        assert "reducer" in str(exc_info.value).lower()
    
    def test_valid_reducers(self, sample_polygon_coordinates):
        """Test all valid reducers"""
        from app.models.schemas import PolygonRequest
        
        valid_reducers = ['mean', 'median', 'min', 'max', 'mode', 'stdDev', 'var', 'sum']
        for reducer in valid_reducers:
            request = ZonalStatsRequest(
                aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
                start_date=date(2020, 1, 1),
                end_date=date(2020, 1, 31),
                reducer=reducer
            )
            assert request.reducer == reducer
    
    def test_scale_validation(self, sample_polygon_coordinates):
        """Test scale validation"""
        from app.models.schemas import PolygonRequest
        
        # Valid scale
        request = ZonalStatsRequest(
            aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 31),
            scale=10
        )
        assert request.scale == 10
        
        # Invalid: scale < 1
        with pytest.raises(ValidationError):
            ZonalStatsRequest(
                aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
                start_date=date(2020, 1, 1),
                end_date=date(2020, 1, 31),
                scale=0
            )


class TestResponseModels:
    """Tests for response models"""
    
    def test_health_response(self):
        """Test HealthResponse model"""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            gee_initialized=True
        )
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.gee_initialized is True
    
    def test_ndvi_response(self):
        """Test NDVIResponse model"""
        response = NDVIResponse(
            status="success",
            message="Collection information retrieved successfully",
            data={"collection_size": 10}
        )
        assert response.status == "success"
        assert response.data["collection_size"] == 10
    
    def test_zonal_stats_response(self):
        """Test ZonalStatsResponse model"""
        response = ZonalStatsResponse(
            status="success",
            message="Zonal statistics computed successfully",
            records_count=5,
            data=[{"NDVI": 0.65}, {"NDVI": 0.72}]
        )
        assert response.status == "success"
        assert response.records_count == 5
        assert len(response.data) == 2

