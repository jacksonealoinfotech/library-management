import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory: library-management-system/
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./library.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-prod-min-32-chars")
    SESSION_EXPIRE_MINUTES: int = int(os.getenv("SESSION_EXPIRE_MINUTES", "60"))
    MAX_BOOKS_PER_STUDENT: int = int(os.getenv("MAX_BOOKS_PER_STUDENT", "3"))
    FINE_PER_DAY: float = float(os.getenv("FINE_PER_DAY", "5.0"))
    LIBRARY_NAME: str = os.getenv("LIBRARY_NAME", "Central Library")
    DEFAULT_DUE_DAYS: int = int(os.getenv("DEFAULT_DUE_DAYS", "14"))
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"
    STATIC_DIR: Path = BASE_DIR / "app" / "static"

settings = Settings()
