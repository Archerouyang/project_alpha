# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from dotenv import load_dotenv

# Explicitly load .env from the current working directory or parent directories.
# override=True ensures .env vars take precedence over existing env vars if they are also in the environment.
load_dotenv(verbose=True, override=True)

class Settings(BaseSettings):
    APP_NAME: str = "Project Alpha AI Technical Analysis Service"
    DEBUG: bool = False

    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = "YOUR_OPENAI_API_KEY_HERE"
    GEMINI_API_KEY: Optional[str] = "YOUR_GEMINI_API_KEY_HERE"
    DEEPSEEK_API_KEY: Optional[str] = None

    # Data Provider API Keys
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    FMP_API_KEY: Optional[str] = None

    # Chart Generation Config
    TRADINGVIEW_CHART_WIDTH: int = 1200
    TRADINGVIEW_CHART_HEIGHT: int = 800

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

# Instantiate settings to be imported by other modules
settings = Settings()

# Simple startup checks for essential keys
if not settings.FMP_API_KEY:
    print("CRITICAL WARNING: FMP_API_KEY is not set.")
if not settings.DEEPSEEK_API_KEY:
    print("CRITICAL WARNING: DEEPSEEK_API_KEY is not set.") 