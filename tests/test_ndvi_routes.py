"""
Unit tests for NDVI API endpoints
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from app.models.schemas import PolygonRequest


class TestNDVIRoutes:
    """Tests for NDVI API endpoints"""
    
    def test_zonal_stats_endpoint_success(self, client, mock_ee_initialized, sample_polygon_coordinates):
        """Test successful zonal stats endpoint"""
        request_data = {
            "aoi": {
                "coordinates": sample_polygon_coordinates
            },
            "start_date": "2020-01-01",
            "end_date": "2020-01-31",
            "bands": ["B4", "B8"],
            "cloud_filter": 60,
            "reducer": "mean",
            "scale": 10
        }
        
        with patch('app.routers.ndvi.NDVIService.compute_ndvi_zonal_stats') as mock_service:
            mock_service.return_value = {
                "records": [
                    {"imageID": "img1", "Date": "01-01-2020", "NDVI": 0.65},
                    {"imageID": "img2", "Date": "02-01-2020", "NDVI": 0.72}
                ],
                "count": 2,
                "columns": ["imageID", "Date", "NDVI"]
            }
            
            response = client.post("/api/v1/ndvi/zonal-stats", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["records_count"] == 2
            assert len(data["data"]) == 2
            assert data["data"][0]["NDVI"] == 0.65
    
    def test_zonal_stats_endpoint_validation_error(self, client, mock_ee_initialized):
        """Test zonal stats endpoint with invalid request"""
        # Invalid: polygon not closed
        request_data = {
            "aoi": {
                "coordinates": [
                    [75.7089111013882, 31.37279750147279],
                    [75.7089111013882, 31.371250459643193],
                    [75.71048323497394, 31.371250459643193],
                    [75.71048323497394, 31.37279750147279]
                ]
            },
            "start_date": "2020-01-01",
            "end_date": "2020-01-31",
            "reducer": "mean"
        }
        
        response = client.post("/api/v1/ndvi/zonal-stats", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_zonal_stats_endpoint_service_exception(self, client, mock_ee_initialized, sample_polygon_coordinates):
        """Test zonal stats endpoint when service raises exception"""
        request_data = {
            "aoi": {
                "coordinates": sample_polygon_coordinates
            },
            "start_date": "2020-01-01",
            "end_date": "2020-01-31",
            "reducer": "mean"
        }
        
        with patch('app.routers.ndvi.NDVIService.compute_ndvi_zonal_stats') as mock_service:
            mock_service.side_effect = Exception("Service error")
            
            response = client.post("/api/v1/ndvi/zonal-stats", json=request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to compute zonal statistics" in data["detail"]
    
    def test_collection_info_endpoint_success(self, client, mock_ee_initialized, sample_polygon_coordinates):
        """Test successful collection info endpoint"""
        request_data = {
            "aoi": {
                "coordinates": sample_polygon_coordinates
            },
            "start_date": "2020-01-01",
            "end_date": "2020-01-31",
            "bands": ["B4", "B8"],
            "cloud_filter": 60
        }
        
        with patch('app.routers.ndvi.NDVIService.get_ndvi_collection_info') as mock_service:
            mock_service.return_value = {
                "collection_size": 10,
                "date_range": {
                    "start": "2020-01-01",
                    "end": "2020-01-31"
                },
                "bands": ["B4", "B8"],
                "aoi_coordinates": sample_polygon_coordinates
            }
            
            response = client.post("/api/v1/ndvi/collection-info", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["collection_size"] == 10
            assert data["data"]["bands"] == ["B4", "B8"]
    
    def test_collection_info_endpoint_service_exception(self, client, mock_ee_initialized, sample_polygon_coordinates):
        """Test collection info endpoint when service raises exception"""
        request_data = {
            "aoi": {
                "coordinates": sample_polygon_coordinates
            },
            "start_date": "2020-01-01",
            "end_date": "2020-01-31"
        }
        
        with patch('app.routers.ndvi.NDVIService.get_ndvi_collection_info') as mock_service:
            mock_service.side_effect = Exception("Service error")
            
            response = client.post("/api/v1/ndvi/collection-info", json=request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to get collection info" in data["detail"]
    
    def test_zonal_stats_invalid_reducer(self, client, mock_ee_initialized, sample_polygon_coordinates):
        """Test zonal stats with invalid reducer"""
        request_data = {
            "aoi": {
                "coordinates": sample_polygon_coordinates
            },
            "start_date": "2020-01-01",
            "end_date": "2020-01-31",
            "reducer": "invalid_reducer"
        }
        
        response = client.post("/api/v1/ndvi/zonal-stats", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_zonal_stats_invalid_scale(self, client, mock_ee_initialized, sample_polygon_coordinates):
        """Test zonal stats with invalid scale"""
        request_data = {
            "aoi": {
                "coordinates": sample_polygon_coordinates
            },
            "start_date": "2020-01-01",
            "end_date": "2020-01-31",
            "scale": 0  # Invalid: must be >= 1
        }
        
        response = client.post("/api/v1/ndvi/zonal-stats", json=request_data)
        assert response.status_code == 422  # Validation error

