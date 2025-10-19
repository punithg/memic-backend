from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional, Literal
import os


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Environment settings
    app_env: Literal["dev", "uat", "prod"] = Field(default="dev", env="APP_ENV")
    
    # Database settings
    database_url: str = Field(default="postgresql+psycopg://punithg@localhost:5432/memic_dev", env="DATABASE_URL")
    
    # Application settings
    app_name: str = Field(default="Memic Backend", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # API Keys and Secrets
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    jwt_secret_key: Optional[str] = Field(default=None, env="JWT_SECRET_KEY")
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    
    # Third-party service keys
    stripe_secret_key: Optional[str] = Field(default=None, env="STRIPE_SECRET_KEY")
    sendgrid_api_key: Optional[str] = Field(default=None, env="SENDGRID_API_KEY")
    
    # Environment-specific settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    
    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment is one of the allowed values."""
        allowed_envs = ["dev", "uat", "prod"]
        if v not in allowed_envs:
            raise ValueError(f"APP_ENV must be one of {allowed_envs}")
        return v
    
    @field_validator("openai_api_key", "jwt_secret_key", "encryption_key")
    @classmethod
    def validate_required_secrets(cls, v, info):
        """Validate required secrets are present based on environment."""
        # Get the current environment from the model
        env = os.getenv("APP_ENV", "dev")
        
        # In production environments, these secrets are required
        if env in ["uat", "prod"] and not v:
            raise ValueError(f"{info.field_name} is required in {env} environment")
        
        return v
    
    def get_environment_file(self) -> str:
        """Get the appropriate environment file based on APP_ENV."""
        env_files = {
            "dev": ".env.dev",
            "uat": ".env.uat", 
            "prod": ".env.prod"
        }
        return env_files.get(self.app_env, ".env.dev")
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "prod"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "dev"
    
    class Config:
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

