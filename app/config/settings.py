import os
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application configuration from environment variables."""
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://ai_platform:password@localhost:5432/ai_job_impact"
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API
    api_port: int = int(os.getenv("API_PORT", 8000))
    api_workers: int = int(os.getenv("API_WORKERS", 4))
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
    ]
    
    # Model
    model_path: str = "models/checkpoints/xgboost_model.pkl"
    use_cache: bool = True
    cache_ttl: int = 86400  # 24 hours
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()