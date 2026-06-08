"""Configuration settings for the application"""
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Info
    APP_NAME: str = "Smart Resume Maker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Keys
    OPENAI_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "us-west1-gcp"
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()


