# backend/core/data_fetcher.py
import pandas as pd
import asyncio
import os
from datetime import datetime, timedelta, date
from typing import Tuple, List, Optional, Dict, Any
from openbb import obb
from dotenv import load_dotenv
import math

# Load environment variables from .env file at the module level
load_dotenv()

# This file is now a collection of functions, not a class.

def _get_fmp_api_key() -> Optional[str]:
    """
    Reads the FMP API key from the .env file in the project root.
    """
    try:
        # Construct the path to the .env file relative to this script
        # __file__ -> backend/core/data_fetcher.py
        # os.path.dirname(__file__) -> backend/core
        # ... -> project_alpha/
        dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
        if not os.path.exists(dotenv_path):
            print(f"Warning: .env file not found at {dotenv_path}")
            return None
        
        with open(dotenv_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key.strip() == 'FMP_API_KEY':
                        # Remove potential quotes from the value
                        return value.strip().strip('"\'')
        return None
    except Exception as e:
        print(f"Error reading .env file: {e}")
        return None

def map_interval_to_openbb(interval_str: str) -> str:
    """Maps common interval strings to OpenBB's expected 'interval' enum where possible."""
    interval_lower = interval_str.lower()
    if interval_lower in ["1m", "1min"]: return "1m"
    if interval_lower in ["5m", "5min"]: return "5m"
    if interval_lower in ["15m", "15min"]: return "15m"
    if interval_lower in ["30m", "30min"]: return "30m"
    if interval_lower in ["1h", "60m", "60min", "1hour"]: return "1h"
    if interval_lower in ["4h", "240m", "4hour"]: return "4h"
    if interval_lower in ["1d", "1day", "daily"]: return "1d"
    if interval_lower in ["1w", "1wk", "1week", "weekly"]: return "1w"
    if interval_lower in ["1mo", "1month", "monthly"]: return "1mo"
    return interval_str

def _standardize_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes the column names of the OHLCV DataFrame."""
    rename_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'open' in col_lower: rename_map[col] = 'open'
        elif 'high' in col_lower: rename_map[col] = 'high'
        elif 'low' in col_lower: rename_map[col] = 'low'
        elif 'adj close' in col_lower: rename_map[col] = 'close'
        elif 'close' in col_lower:
            if 'close' not in rename_map.values(): rename_map[col] = 'close'
        elif 'volume' in col_lower: rename_map[col] = 'volume'
    df.rename(columns=rename_map, inplace=True)
    
    # Ensure all required columns are present
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            if col == 'volume':
                df['volume'] = 0
            else:
                raise ValueError(f"Missing required column '{col}' after standardization.")
    return df[required_cols]

CRYPTO_EXCHANGES = ["coinbase", "binance", "kraken", "kucoin", "gateio", "fmp"]

def get_ohlcv_data(
    ticker: str,
    interval: str,
    num_candles: int = 150
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Fetches OHLCV data for a given ticker, ensuring a specific number of candles.
    It over-fetches data based on a rough estimate and then trims to the exact number.
    This is now a synchronous function.
    """
    print(f"Fetching data for '{ticker}': aiming for {num_candles} candles, interval '{interval}'...")

    # --- JIT Credential Setup ---
    # Set credentials right before the API call to ensure they are available
    # in any execution context (main app or subprocess).
    fmp_api_key = os.getenv("FMP_API_KEY")
    if not fmp_api_key:
        # This is a critical error, as the API call will fail.
        print("CRITICAL: FMP_API_KEY not found in environment. Aborting data fetch.")
        raise ValueError("Missing FMP_API_KEY. Ensure it's in the .env file and loaded correctly.")
    obb.user.credentials.fmp_api_key = fmp_api_key
    
    # Estimate days to fetch. Add a 50% buffer to account for non-trading days/hours.
    candles_per_day_map = {
        '1d': 1,
        '4h': 2, # ~ 6.5h trading day / 4h = 1.625 -> 2
        '1h': 7  # ~ 6.5h trading day / 1h = 6.5 -> 7
    }
    candles_per_day = candles_per_day_map.get(interval, 1) # Default to 1 for unknown intervals
    
    # Calculate days to fetch with a 1.5x buffer, ensuring at least a few days are fetched.
    days_to_fetch = math.ceil((num_candles / candles_per_day) * 1.5) + 2

    start_date = (datetime.now() - timedelta(days=days_to_fetch)).strftime('%Y-%m-%d')
    
    try:
        # Use OpenBB SDK to fetch data - this is a synchronous call, so no 'await'.
        data = obb.equity.price.historical(
            symbol=ticker,
            start_date=start_date,
            interval=interval,
            provider="fmp"
        )
        
        # Convert the OpenBB object to a pandas DataFrame immediately.
        df = data.to_df()

        # Now, all checks should be performed on the DataFrame.
        if df.empty:
            print(f"No data fetched for ticker {ticker} (DataFrame is empty).")
            return None, None

        # Sort by date to ensure chronological order before trimming
        df.sort_index(ascending=True, inplace=True)

        # Trim the DataFrame to the desired number of candles
        if len(df) > num_candles:
            df_trimmed = df.tail(num_candles).copy()
        else:
            df_trimmed = df.copy()

        print(f"Successfully fetched {len(df_trimmed)} data points for '{ticker}'.")
        
        # The first element of the tuple is the raw, untrimmed data (for potential future use)
        # The second is the processed, trimmed data which we will use.
        return df, df_trimmed

    except Exception as e:
        print(f"An error occurred while fetching data for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return None, None