import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Real-Time AI Visual Detection System"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    EVIDENCE_DIR: str = os.getenv("EVIDENCE_DIR", "./evidence")
    PHONE_CONFIDENCE_THRESHOLD: float = 0.30
    PERSON_CONFIDENCE_THRESHOLD: float = 0.55

    # SMTP Real Email Transport Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

settings = Settings()

os.makedirs(settings.EVIDENCE_DIR, exist_ok=True)
