"""
Pytest configuration and shared fixtures
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def mock_ee_initialized():
    """Mock Earth Engine initialization"""
    with patch('app.core.dependencies.get_ee_initialized', return_value=True):
        yield


@pytest.fixture
def sample_polygon_coordinates():
    """Sample polygon coordinates for testing"""
    return [
        [75.7089111013882, 31.37279750147279],
        [75.7089111013882, 31.371250459643193],
        [75.71048323497394, 31.371250459643193],
        [75.71048323497394, 31.37279750147279],
        [75.7089111013882, 31.37279750147279]  # Closed polygon
    ]


@pytest.fixture
def sample_ndvi_request(sample_polygon_coordinates):
    """Sample NDVI request data"""
    from app.models.schemas import NDVIRequest, PolygonRequest
    from datetime import date
    
    return NDVIRequest(
        aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
        start_date=date(2020, 1, 1),
        end_date=date(2020, 1, 31),
        bands=["B4", "B8"],
        cloud_filter=60
    )


@pytest.fixture
def sample_zonal_stats_request(sample_polygon_coordinates):
    """Sample zonal stats request data"""
    from app.models.schemas import ZonalStatsRequest, PolygonRequest
    from datetime import date
    
    return ZonalStatsRequest(
        aoi=PolygonRequest(coordinates=sample_polygon_coordinates),
        start_date=date(2020, 1, 1),
        end_date=date(2020, 1, 31),
        bands=["B4", "B8"],
        cloud_filter=60,
        reducer="mean",
        scale=10
    )


@pytest.fixture
def mock_ee():
    """Mock Earth Engine module"""
    with patch('app.services.ndvi_service.ee') as mock_ee:
        # Mock common EE objects
        mock_ee.Geometry.Polygon.return_value = MagicMock()
        mock_ee.FeatureCollection.return_value = MagicMock()
        mock_ee.Feature.return_value = MagicMock()
        mock_ee.Number.return_value = MagicMock()
        mock_ee.Number.return_value.getInfo.return_value = 1
        yield mock_ee

