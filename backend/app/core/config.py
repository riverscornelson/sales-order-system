import os
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Application
    app_name: str = "Sales Order Entry System"
    debug: bool = False
    environment: str = "production"
    
    # Alias for backward compatibility
    @property
    def ENVIRONMENT(self) -> str:
        return self.environment
    
    @property
    def LOG_LEVEL(self) -> str:
        return "DEBUG" if self.debug else "INFO"
    
    # Database
    database_url: Optional[str] = None
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Google Cloud
    google_cloud_project: Optional[str] = None
    
    # Storage
    uploads_bucket: Optional[str] = None
    vectors_bucket: Optional[str] = None
    
    # Dynamics ERP (optional)
    dynamics_tenant_id: Optional[str] = None
    dynamics_client_id: Optional[str] = None
    dynamics_client_secret: Optional[str] = None
    dynamics_resource_url: Optional[str] = None
    use_mock_erp: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields without validation errors


# Global settings instance
settings = Settings()