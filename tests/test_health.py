"""
Unit tests for health check endpoint
"""
import pytest
from unittest.mock import patch, MagicMock
from app.models.schemas import HealthResponse


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check_success(self, client, mock_ee_initialized):
        """Test successful health check"""
        with patch('app.routers.health.ee') as mock_ee:
            mock_ee.Number.return_value = MagicMock()
            mock_ee.Number.return_value.getInfo.return_value = 1
            
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data
            assert data["gee_initialized"] is True
    
    def test_health_check_gee_not_initialized(self, client, mock_ee_initialized):
        """Test health check when GEE is not initialized"""
        with patch('app.routers.health.ee') as mock_ee:
            mock_ee.Number.return_value = MagicMock()
            mock_ee.Number.return_value.getInfo.side_effect = Exception("Not initialized")
            
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"  # Service is still healthy
            assert data["gee_initialized"] is False
    
    def test_health_check_response_structure(self, client, mock_ee_initialized):
        """Test health check response structure"""
        with patch('app.routers.health.ee') as mock_ee:
            mock_ee.Number.return_value = MagicMock()
            mock_ee.Number.return_value.getInfo.return_value = 1
            
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            data = response.json()
            
            # Verify all required fields
            assert "status" in data
            assert "version" in data
            assert "gee_initialized" in data
            assert isinstance(data["status"], str)
            assert isinstance(data["version"], str)
            assert isinstance(data["gee_initialized"], bool)
    
    def test_health_check_exception_handling(self, client, mock_ee_initialized):
        """Test health check exception handling - GEE failure doesn't make service unhealthy"""
        with patch('app.routers.health.ee') as mock_ee:
            # Simulate GEE check failure - this should not make the service unhealthy
            mock_ee.Number.side_effect = Exception("Unexpected error")
            
            response = client.get("/api/v1/health")
            # Should still return 200, service is healthy even if GEE check fails
            assert response.status_code == 200
            data = response.json()
            # When GEE check fails, service is still healthy, just GEE is not initialized
            assert data["status"] == "healthy"
            assert data["gee_initialized"] is False

