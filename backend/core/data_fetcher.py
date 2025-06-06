# backend/core/data_fetcher.py
import pandas as pd
import asyncio
import os
from datetime import datetime, timedelta
from typing import Tuple, List, Optional, Dict, Any
from openbb import obb
from dotenv import load_dotenv

# Load environment variables from .env file
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

async def get_ohlcv_data(
    ticker_symbol: str,
    days_history: int = 30,
    interval: str = "1d",
    extended_hours: bool = False
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[pd.DataFrame]]:
    """
    Fetches historical OHLCV data using the OpenBB SDK.
    Returns both a data structure formatted for JS charting and the raw pandas DataFrame.

    Args:
        ticker_symbol (str): The stock symbol (e.g., "TSLA").
        days_history (int): Number of past days to fetch data for.
        interval (str): The data interval (e.g., "1h", "4h", "1d").
        extended_hours (bool): Whether to include pre/post market data (for equities).

    Returns:
        A tuple containing:
        - list: A list of dicts formatted for the frontend chart (OHLC & Volume).
        - pd.DataFrame: The raw, unprocessed DataFrame from the provider.
        Returns (None, None) if an error occurs.
    """
    print(f"Fetching data for '{ticker_symbol}': {days_history} days, interval '{interval}'...")
    start_date = (datetime.now() - timedelta(days=days_history)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    openbb_interval = map_interval_to_openbb(interval)
    
    # Manually get the API key
    fmp_api_key = _get_fmp_api_key()
    if not fmp_api_key:
        print("FMP_API_KEY not found in .env file. Aborting data fetch.")
        return None, None

    try:
        # Manually log in to the provider with the key
        obb.user.credentials.fmp_api_key = fmp_api_key
        
        # Using 'fmp' as the default provider for equity data.
        data_obb = await asyncio.to_thread(
            obb.equity.price.historical,
            symbol=ticker_symbol,
            start_date=start_date,
            end_date=end_date,
            interval=openbb_interval,
            provider="fmp",
            extended_hours=extended_hours
        )

        if not hasattr(data_obb, 'to_dataframe') or data_obb.to_dataframe().empty:
            print(f"OpenBB returned no data for '{ticker_symbol}'.")
            return None, None

        raw_df = data_obb.to_dataframe()
        # The raw_df is returned for indicator calculations
        print(f"Successfully fetched {len(raw_df)} data points for '{ticker_symbol}'.")
        
        # This part formats the data specifically for the chart rendering
        df_for_js = raw_df.copy()
        df_for_js.columns = [col.lower() for col in df_for_js.columns]
        
        ohlc_data = []
        volume_data = []
        for timestamp, row in df_for_js.iterrows():
            time_unix = int(timestamp.timestamp())
            ohlc_data.append({
                "time": time_unix,
                "open": row['open'],
                "high": row['high'],
                "low": row['low'],
                "close": row['close']
            })
            volume_color = 'rgba(0, 150, 136, 0.6)' if row['close'] >= row['open'] else 'rgba(255, 82, 82, 0.6)'
            volume_data.append({"time": time_unix, "value": row['volume'], "color": volume_color})

        js_data = {
            "ohlcData": ohlc_data,
            "volumeData": volume_data
        }

        return js_data, raw_df

    except Exception as e:
        print(f"An error occurred during OpenBB data fetch for '{ticker_symbol}': {e}")
        return None, None