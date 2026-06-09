from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
import os


# Load .env from the project root, regardless of where uvicorn is started.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    MASSIVE_API_KEY: str | None = os.getenv("MASSIVE_API_KEY")
    MASSIVE_BASE_URL: str = os.getenv("MASSIVE_BASE_URL", "https://api.massive.com")

    # Future AWS/data-engineering settings.
    AWS_REGION: str | None = os.getenv("AWS_REGION")
    S3_RAW_BUCKET: str | None = os.getenv("S3_RAW_BUCKET")
    S3_CURATED_BUCKET: str | None = os.getenv("S3_CURATED_BUCKET")
    ATHENA_DATABASE: str | None = os.getenv("ATHENA_DATABASE")
    REDSHIFT_HOST: str | None = os.getenv("REDSHIFT_HOST")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    FRED_API_KEY: str | None = os.getenv("FRED_API_KEY")
@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
