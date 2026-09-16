"""
Core Configuration Module for AI Remote Proctoring System
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """System-wide configuration settings with environment variable fallbacks."""
    
    PROJECT_NAME: str = "AI Remote Proctoring System"
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")))
    APP_ENV: str = Field(default_factory=lambda: os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")))
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    API_PORT: int = Field(default_factory=lambda: int(os.getenv("API_PORT", "8001")))
    API_HOST: str = Field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    
    # Gemini API Credentials
    GEMINI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    GEMINI_MODEL_ID: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL_ID", os.getenv("GEMINI_MODEL", "gemini-2.5-flash")))
    
    # AWS / S3 Storage Credentials
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID"))
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY"))
    AWS_REGION: str = Field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    S3_BUCKET_NAME: str = Field(default_factory=lambda: os.getenv("S3_BUCKET_NAME", "proctor-session-media"))
    
    # Database & Cache URIs
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/proctoring_db"
        )
    )
    REDIS_URL: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    
    # Biometric Verification Thresholds
    MIN_FACE_MATCH_THRESHOLD: float = Field(
        default_factory=lambda: float(os.getenv("MIN_FACE_MATCH_THRESHOLD", "0.70"))
    )  # >= 70% automatically verified
    HUMAN_REVIEW_MATCH_THRESHOLD: float = Field(
        default_factory=lambda: float(os.getenv("HUMAN_REVIEW_MATCH_THRESHOLD", "0.40"))
    )  # 40% - 69.9% escalates to proctor triage
    
    # Proctoring Risk & Violation Thresholds
    MAX_CUMULATIVE_RISK_SCORE: float = 100.0
    WARNING_RISK_THRESHOLD: float = 40.0
    ESCALATE_HUMAN_THRESHOLD: float = 70.0
    TERMINATION_THRESHOLD: float = 90.0
    
    # Media Sampling Settings
    FRAME_SAMPLE_INTERVAL_SECONDS: float = 1.0
    MAX_CONCURRENT_SESSIONS: int = 100


settings = Settings()
