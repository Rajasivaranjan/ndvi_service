import ee
import os
from app.core.config import settings
from functools import lru_cache


@lru_cache()
def get_ee_initialized():
    """Initialize Google Earth Engine if not already initialized"""
    try:
        # Check if already initialized
        ee.Number(1).getInfo()
        return True
    except Exception:
        # Initialize if not already done
        try:
            if settings.gee_credentials_path and settings.gee_service_account:
                # Use service account credentials
                credentials = ee.ServiceAccountCredentials(
                    settings.gee_service_account,
                    settings.gee_credentials_path
                )
                if settings.gee_project:
                    ee.Initialize(credentials, project=settings.gee_project)
                else:
                    ee.Initialize(credentials)
            elif settings.gee_project:
                # Initialize with project name (assumes user is already authenticated)
                ee.Initialize(project=settings.gee_project)
            else:
                # Default initialization (assumes user is already authenticated)
                ee.Initialize()
            return True
        except Exception as e:
            raise Exception(f"Failed to initialize Google Earth Engine: {str(e)}")

