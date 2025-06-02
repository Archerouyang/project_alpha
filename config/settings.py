# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from dotenv import load_dotenv

# Explicitly load .env from the current working directory or parent directories.
# verbose=True will print a message if it loads a file (or which files it tried).
# override=True ensures .env vars take precedence over existing env vars if they are also in the environment.
print(f"[DEBUG settings.py] Current working directory for .env search: {os.getcwd()}")
# python-dotenv's load_dotenv() will search for a .env file in the current working directory
# and then in parent directories. It returns True if a .env file was loaded.
found_dotenv = load_dotenv(verbose=True, override=True)

class Settings(BaseSettings):
    APP_NAME: str = "Project Alpha AI Technical Analysis Service"
    DEBUG: bool = False

    # LLM API Keys - add more as needed
    OPENAI_API_KEY: Optional[str] = "YOUR_OPENAI_API_KEY_HERE"
    GEMINI_API_KEY: Optional[str] = "YOUR_GEMINI_API_KEY_HERE"

    # Data Fetcher Config (if any specific needed beyond yfinance defaults)
    # EXAMPLE_DATA_API_KEY: str = "YOUR_DATA_API_KEY"

    # Chart Generation Config
    TRADINGVIEW_CHART_WIDTH: int = 1200
    TRADINGVIEW_CHART_HEIGHT: int = 800

    # Alpha Vantage API Key
    # Load from .env file. Environment variable name should be ALPHA_VANTAGE_API_KEY
    ALPHA_VANTAGE_API_KEY: Optional[str] = None

    # Financial Modeling Prep API Key
    FMP_API_KEY: Optional[str] = None

    # To load variables from a .env file (in the config/ directory)
    # The .env file should be in the same directory as this settings.py for this model_config
    # or adjust the path if .env is at project root.
    model_config = SettingsConfigDict(
        env_file='.env', # Pydantic will also look for .env in CWD (after checking actual env vars)
        env_file_encoding='utf-8',
        extra='ignore'
    )

# Instantiate settings to be imported by other modules
settings = Settings()

# --- REMOVE DEBUG BLOCK ---
# print(f"[DEBUG settings.py] python-dotenv load_dotenv() call returned: {found_dotenv}")
# if found_dotenv:
#     print(f"[DEBUG settings.py] A .env file was loaded by python-dotenv.")
# else:
#     print(f"[DEBUG settings.py] No .env file was loaded by python-dotenv (searched in CWD: '{os.getcwd()}' and parent dirs).")
#     
#     expected_dotenv_path = os.path.join(os.getcwd(), ".env")
#     if not os.path.exists(expected_dotenv_path):
#         print(f"[DEBUG settings.py] The file {expected_dotenv_path} does NOT exist.")
#     else:
#         print(f"[DEBUG settings.py] The file {expected_dotenv_path} DOES exist, but python-dotenv didn't load it (check permissions or content?).")
# 
# print(f"[DEBUG settings.py] Value of ALPHA_VANTAGE_API_KEY from os.environ after load_dotenv: '{os.getenv('ALPHA_VANTAGE_API_KEY')}'")
# print(f"[DEBUG settings.py] Value of settings.ALPHA_VANTAGE_API_KEY after Pydantic instantiation: '{settings.ALPHA_VANTAGE_API_KEY}'")
# print(f"[DEBUG settings.py] Loaded settings.ALPHA_VANTAGE_API_KEY: '{settings.ALPHA_VANTAGE_API_KEY}'") # This was a duplicate line
# --- END REMOVE DEBUG BLOCK ---

if not settings.ALPHA_VANTAGE_API_KEY:
    print("--------------------------------------------------------------------------------------")
    print("CRITICAL WARNING: settings.ALPHA_VANTAGE_API_KEY is not set.")
    if not found_dotenv:
        print("Reason: python-dotenv did not find and load a .env file.")
    elif not os.getenv('ALPHA_VANTAGE_API_KEY'):
        print("Reason: .env file was loaded, but ALPHA_VANTAGE_API_KEY was not found in it or os.environ.")
    else:
        print("Reason: ALPHA_VANTAGE_API_KEY was in os.environ, but Pydantic didn't pick it up (unlikely).")
    
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure your .env file exists in the project root (same directory as pyproject.toml)")
    print("and contains the line: ALPHA_VANTAGE_API_KEY=YOUR_ACTUAL_KEY_HERE")
    print("--------------------------------------------------------------------------------------")

# Removed lru_cache and get_settings() for this simplified direct instantiation model
# If settings were more complex or dynamically configured, get_settings() with caching would be useful.

# You can access settings in your app like this:
# from config.settings import get_settings
# settings = get_settings()
# print(settings.OPENAI_API_KEY)

# Instantiate settings to be imported by other modules
settings = Settings()

# --- BEGIN DEBUG PRINT ---
print(f"[DEBUG settings.py] Loaded settings.ALPHA_VANTAGE_API_KEY: '{settings.ALPHA_VANTAGE_API_KEY}'")
print(f"[DEBUG settings.py] Loaded settings.FMP_API_KEY: '{settings.FMP_API_KEY}'")
# --- END DEBUG PRINT ---

# You can add a simple check here for critical settings if needed when settings.py is loaded
if not settings.ALPHA_VANTAGE_API_KEY:
    print("--------------------------------------------------------------------------------------")
    print("CRITICAL WARNING: ALPHA_VANTAGE_API_KEY is not set in the environment or .env file.")
    print(f"Pydantic is looking for the .env file at: {Settings.model_config.get('env_file')}")
    print("Please create a .env file in the project root with your Alpha Vantage API key:")
    print("Example .env content: ALPHA_VANTAGE_API_KEY=YOUR_ACTUAL_KEY_HERE")
    print("--------------------------------------------------------------------------------------") 