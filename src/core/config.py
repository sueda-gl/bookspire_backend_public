from pydantic_settings import BaseSettings
from pydantic import validator
from functools import lru_cache
from typing import List, Optional, Union, Dict, Any
import os

class BaseConfig(BaseSettings):
    """
    Base configuration with common settings across all environments.
    Values are loaded from environment variables and validated.
    """
    # Application
    APP_NAME: str = "Sherlock Holmes Learning App"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Security (MUST be set in environment variables - defaults will raise errors)
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # LLM API
    OPENAI_API_KEY: str  # Required, no default
    MODEL_NAME: str = "gpt-4o-mini"
    MAX_TOKENS: int = 500
    TEMPERATURE: float = 0.5
    
    # Redis
    REDIS_URL: str

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Generate async database URL from standard URL for SQLAlchemy"""
        # First, remove any sslmode parameter as asyncpg handles SSL differently
        base_url = self.DATABASE_URL
        
        # Remove the sslmode parameter if present
        if "?sslmode=" in base_url:
            base_url = base_url.split("?sslmode=")[0]
        
        # Convert to asyncpg format
        async_url = base_url.replace("postgresql://", "postgresql+asyncpg://")
        
        return async_url
    
    @validator("OPENAI_API_KEY", pre=True)
    def validate_openai_key(cls, v):
        if not v:
            raise ValueError("OPENAI_API_KEY must be set")
        return v
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v):
        if not v:
            raise ValueError("SECRET_KEY must be set")
        return v
    
    @validator("JWT_SECRET_KEY", pre=True)
    def validate_jwt_secret_key(cls, v):
        if not v:
            raise ValueError("JWT_SECRET_KEY must be set")
        return v
    
    @validator("REDIS_URL", pre=True)
    def validate_redis_url(cls, v):
        if not v:
            raise ValueError("REDIS_URL must be set")
        return v
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Handle CORS_ORIGINS as comma-separated string or list"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # This allows Pydantic to populate the config using environment
        # variables that match field names (e.g., REDIS_URL)


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    DEBUG: bool = True
    
    # Development can use less secure local defaults if not provided
    DATABASE_URL: str = "postgresql://school_admin:ilgin@localhost:5432/school_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"


class ProductionConfig(BaseConfig):
    """Production environment configuration with stricter security."""
    DEBUG: bool = False
    
    DATABASE_URL: str
    
    class Config:
        env_file = ".env"


class TestConfig(BaseConfig):
    """Test environment configuration."""
    DEBUG: bool = True
    TESTING: bool = True
    
    # Test databases
    DATABASE_URL: str = "postgresql://school_admin:ilgin@localhost:5432/test_db"
    REDIS_URL: str = "redis://localhost:6379/1"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Union[DevelopmentConfig, ProductionConfig, TestConfig]:
    """
    Factory function that returns the appropriate settings object based on the environment.
    Cached to avoid re-reading environment variables on every call.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionConfig()
    elif environment == "testing":
        return TestConfig()
    else:
        return DevelopmentConfig()


# Export the settings instance for easy import
settings = get_settings()