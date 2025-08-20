import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Keys
    SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # API Configuration
    SPORTMONKS_BASE_URL = os.getenv("SPORTMONKS_BASE_URL", "https://api.sportmonks.com/v3")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./soccer_scout.db")
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

settings = Settings()