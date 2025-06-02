# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Project Alpha AI Technical Analysis Service"
    DEBUG: bool = False

    # LLM API Keys - add more as needed
    OPENAI_API_KEY: str = "YOUR_OPENAI_API_KEY_HERE"
    GEMINI_API_KEY: str = "YOUR_GEMINI_API_KEY_HERE"

    # Data Fetcher Config (if any specific needed beyond yfinance defaults)
    # EXAMPLE_DATA_API_KEY: str = "YOUR_DATA_API_KEY"

    # Chart Generation Config
    TRADINGVIEW_CHART_WIDTH: int = 1200
    TRADINGVIEW_CHART_HEIGHT: int = 800

    # To load variables from a .env file (in the config/ directory)
    # The .env file should be in the same directory as this settings.py for this model_config
    # or adjust the path if .env is at project root.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

@lru_cache()
def get_settings() -> Settings:
    """
    Returns the application settings.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()

# You can access settings in your app like this:
# from config.settings import get_settings
# settings = get_settings()
# print(settings.OPENAI_API_KEY) 