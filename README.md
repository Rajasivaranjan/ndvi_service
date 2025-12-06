# NDVI Service

A FastAPI microservice for computing Normalized Difference Vegetation Index (NDVI) using Google Earth Engine and Sentinel-2 satellite imagery.

## Features

- **NDVI Computation**: Calculate NDVI from Sentinel-2 L2A data
- **Zonal Statistics**: Compute statistical summaries (mean, median, min, max, etc.) for areas of interest
- **Cloud Filtering**: Advanced cloud and shadow masking using s2cloudless
- **RESTful API**: Clean, documented API endpoints with automatic OpenAPI documentation
- **Google Earth Engine Integration**: Leverages GEE for scalable geospatial processing

## Prerequisites

- Python 3.9+
- Google Earth Engine account (sign up at https://earthengine.google.com/)
- Authenticated Google Earth Engine credentials

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ndvi_service
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Google Earth Engine:
   - Authenticate using: `earthengine authenticate`
   - Or configure service account credentials (see Configuration)
   
   **Troubleshooting Authentication:**
   If you encounter an error about missing `cloud-platform` scope when running `earthengine authenticate`, 
   first run this command to set up application default credentials with the correct scopes:
   ```bash
   gcloud auth application-default login --scopes=https://www.googleapis.com/auth/earthengine,https://www.googleapis.com/auth/devstorage.full_control,https://www.googleapis.com/auth/cloud-platform
   ```
   Then complete the browser-based authentication by visiting the URL provided when you run `earthengine authenticate --auth_mode=notebook`

5. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
# Application Settings
APP_NAME=NDVI Service
APP_VERSION=1.0.0
DEBUG=false

# Google Earth Engine Settings
GEE_PROJECT=your-project-id

# Or use service account for production:
# GEE_SERVICE_ACCOUNT=your-service-account@project.iam.gserviceaccount.com
# GEE_CREDENTIALS_PATH=/path/to/service-account-key.json

# API Settings
API_PREFIX=/api/v1
CORS_ORIGINS=["*"]
```

## Running the Service

### Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check

**GET** `/api/v1/health`

Check service health and Google Earth Engine initialization status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "gee_initialized": true
}
```

### Compute NDVI Zonal Statistics

**POST** `/api/v1/ndvi/zonal-stats`

Compute zonal statistics for NDVI over an area of interest.

**Request Body:**
```json
{
  "aoi": {
    "coordinates": [
      [75.7089111013882, 31.37279750147279],
      [75.7089111013882, 31.371250459643193],
      [75.71048323497394, 31.371250459643193],
      [75.71048323497394, 31.37279750147279],
      [75.7089111013882, 31.37279750147279]
    ]
  },
  "start_date": "2020-01-01",
  "end_date": "2021-01-31",
  "bands": ["B4", "B8"],
  "cloud_filter": 60,
  "cld_prb_thresh": 20,
  "reducer": "mean",
  "scale": 10
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Zonal statistics computed successfully",
  "records_count": 15,
  "data": [
    {
      "imageID": "COPERNICUS/S2_SR_HARMONIZED/20200101T...",
      "Date": "01-01-2020",
      "NDVI": 0.65
    },
    ...
  ]
}
```

### Get Collection Info

**POST** `/api/v1/ndvi/collection-info`

Get metadata about the Sentinel-2 collection without computing statistics.

**Request Body:**
```json
{
  "aoi": {
    "coordinates": [
      [75.7089111013882, 31.37279750147279],
      [75.7089111013882, 31.371250459643193],
      [75.71048323497394, 31.371250459643193],
      [75.71048323497394, 31.37279750147279],
      [75.7089111013882, 31.37279750147279]
    ]
  },
  "start_date": "2020-01-01",
  "end_date": "2021-01-31",
  "bands": ["B4", "B8"],
  "cloud_filter": 60
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Collection information retrieved successfully",
  "data": {
    "collection_size": 45,
    "date_range": {
      "start": "2020-01-01",
      "end": "2021-01-31"
    },
    "bands": ["B4", "B8"],
    "aoi_coordinates": [...]
  }
}
```

## Request Parameters

### PolygonRequest
- `coordinates`: List of [longitude, latitude] pairs forming a closed polygon (first and last points must be identical)

### NDVIRequest
- `aoi`: Area of Interest polygon
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `bands`: List of Sentinel-2 bands (default: ["B4", "B8"])
- `cloud_filter`: Maximum cloud percentage 0-100 (default: 60)
- `cld_prb_thresh`: Cloud probability threshold 0-100 (default: 20)
- `nir_drk_thresh`: Dark NIR threshold 0-1 (default: 0.15)
- `cld_prj_dist`: Cloud shadow projection distance (default: 1.0)
- `buffer`: Buffer size for cloud mask dilation (default: 50)

### ZonalStatsRequest (extends NDVIRequest)
- `reducer`: Statistical reducer - "mean", "median", "min", "max", "mode", "stdDev", "var", "sum" (default: "mean")
- `scale`: Scale in meters for computation (default: 10)

## Project Structure

```
ndvi_service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration settings
│   │   └── dependencies.py     # Dependency injection
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py           # Health check endpoints
│   │   └── ndvi.py             # NDVI endpoints
│   └── services/
│       ├── __init__.py
│       └── ndvi_service.py     # Business logic
├── GeoKit/
│   ├── raster_classes/
│   │   ├── EERasterBuilder.py
│   │   └── S2L2ACollection.py
│   └── raster_analysis/
│       └── ZonalStats.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_schemas.py         # Schema validation tests
│   ├── test_health.py          # Health endpoint tests
│   ├── test_ndvi_service.py   # Service layer tests
│   └── test_ndvi_routes.py     # API endpoint tests
├── .env.example
├── .gitignore
├── pytest.ini                  # Pytest configuration
├── requirements.txt
└── README.md
```

## Testing

### Unit Tests

Run the test suite using pytest:

```bash
# Install test dependencies (if not already installed)
pip install -r requirements.txt

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py

# Run tests with verbose output
pytest -v
```

The test suite includes:
- **Schema validation tests** (`test_schemas.py`): Tests for Pydantic model validation
- **Health endpoint tests** (`test_health.py`): Tests for health check endpoint
- **NDVI service tests** (`test_ndvi_service.py`): Tests for service layer methods
- **NDVI route tests** (`test_ndvi_routes.py`): Tests for API endpoints

### API Testing

You can test the API using the interactive documentation at `/docs` or with curl:

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Zonal statistics
curl -X POST "http://localhost:8000/api/v1/ndvi/zonal-stats" \
  -H "Content-Type: application/json" \
  -d '{
    "aoi": {
      "coordinates": [[75.7089111013882, 31.37279750147279], ...]
    },
    "start_date": "2020-01-01",
    "end_date": "2021-01-31",
    "reducer": "mean"
  }'
```

## Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t ndvi-service .
docker run -p 8000:8000 --env-file .env ndvi-service
```

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]

## Support

For issues and questions, please open an issue on the repository.

