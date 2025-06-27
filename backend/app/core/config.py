import os
import sys
from typing import Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables.
    
    This class provides secure configuration management with:
    - Environment variable validation
    - Secret masking in logs
    - Required field validation
    - Type safety
    """
    
    # Application
    app_name: str = "Sales Order Entry System"
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="production", pattern="^(development|staging|production)$")
    
    # Alias for backward compatibility
    @property
    def ENVIRONMENT(self) -> str:
        return self.environment
    
    @property
    def LOG_LEVEL(self) -> str:
        return "DEBUG" if self.debug else "INFO"
    
    # Database
    database_url: Optional[str] = None
    
    # OpenAI (Required for AI functionality)
    openai_api_key: str = Field(..., description="OpenAI API key for LLM operations")
    
    @validator('openai_api_key')
    def validate_openai_key(cls, v):
        if not v or v == "REPLACE_WITH_YOUR_API_KEY":
            raise ValueError(
                "OpenAI API key is required. Please set OPENAI_API_KEY environment variable. "
                "Get your key from https://platform.openai.com/"
            )
        if not v.startswith(('sk-', 'sk-proj-')):
            raise ValueError("Invalid OpenAI API key format")
        return v
    
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
        
    def __repr__(self):
        """Safe representation that masks sensitive values."""
        return (
            f"<Settings "
            f"environment={self.environment} "
            f"debug={self.debug} "
            f"openai_configured={'***' if self.openai_api_key else 'False'}>"
        )
    
    def validate_required_settings(self):
        """Validate that all required settings are properly configured."""
        errors = []
        
        if self.environment == "production":
            if self.debug:
                errors.append("DEBUG should be False in production")
            if not self.database_url:
                errors.append("DATABASE_URL is required in production")
        
        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")


# Global settings instance with validation
try:
    settings = Settings()
    settings.validate_required_settings()
except Exception as e:
    print(f"\n❌ Configuration Error: {e}\n", file=sys.stderr)
    print("Please check your .env file and environment variables.", file=sys.stderr)
    print("See .env.example for the required configuration.\n", file=sys.stderr)
    sys.exit(1)