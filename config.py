"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    
    # Google Gemini
    GOOGLE_API_KEY: str
    
    # Email settings
    EMAIL_FROM: str = "noreply@yourcompany.com"
    RESEND_API_KEY: Optional[str] = None
    
    # FAISS settings
    FAISS_INDEX_PATH: str = "data/faiss_index"
    EMBEDDINGS_PATH: str = "data/embeddings"
    
    # Application settings
    MAX_WORKERS: int = 4
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
