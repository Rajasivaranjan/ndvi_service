from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    app_name: str = "NDVI Service"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Google Earth Engine settings
    gee_project: Optional[str] = None
    gee_service_account: Optional[str] = None
    gee_credentials_path: Optional[str] = None
    
    # API settings
    api_prefix: str = "/api/v1"
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

