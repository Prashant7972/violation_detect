import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Real-Time AI Visual Detection System"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    EVIDENCE_DIR: str = os.getenv("EVIDENCE_DIR", "./evidence")
    PHONE_CONFIDENCE_THRESHOLD: float = 0.30
    PERSON_CONFIDENCE_THRESHOLD: float = 0.55

settings = Settings()

os.makedirs(settings.EVIDENCE_DIR, exist_ok=True)
