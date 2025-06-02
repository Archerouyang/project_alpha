# backend/core/data_fetcher.py
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import Tuple, List, Optional, Dict, Any
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.cryptocurrencies import CryptoCurrencies
import time # For potential rate limit handling
from config.settings import settings # Import the settings object

# Use the API key from settings
# ALPHA_VANTAGE_API_KEY = "MZOOXS1S8TXQNOA8" # This will be removed

async def get_ohlcv_data(
    ticker_symbol: str,
    days_history: int = 20,
    interval: str = "1h" # Alpha Vantage: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Optional[pd.DataFrame], Optional[str]]:
    """
    Fetches historical OHLCV data using Alpha Vantage directly,
    formats it for Lightweight Charts, and returns the raw DataFrame.

    Args:
        ticker_symbol (str): The stock/crypto symbol (e.g., "AAPL", "BTC-USD").
        days_history (int): Number of past days to fetch data for.
        interval (str): Data interval (e.g., "1m", "15m", "1h", "4h", "1d").
                         Alpha Vantage supports: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly

    Returns:
        tuple[list, list, pd.DataFrame | None, str | None]:
            - List of dicts for OHLC data: {time, open, high, low, close}
            - List of dicts for Volume data: {time, value, color}
            - Raw pandas DataFrame with DatetimeIndex and ohlcv columns (lowercase), or None on error.
            - Error message string if an error occurs, otherwise None.
    """
    print(f"Fetching data for {ticker_symbol} using Alpha Vantage: {days_history} days, interval {interval}...")
    error_message = None
    raw_df = pd.DataFrame()
    ohlc_js_list = []
    volume_js_list = []

    if not settings.ALPHA_VANTAGE_API_KEY:
        error_message = "ALPHA_VANTAGE_API_KEY not found in settings. Please check .env file."
        print(f"CRITICAL ERROR in data_fetcher: {error_message}")
        return [], [], None, error_message

    ts = TimeSeries(key=settings.ALPHA_VANTAGE_API_KEY, output_format='pandas')
    cc = CryptoCurrencies(key=settings.ALPHA_VANTAGE_API_KEY, output_format='pandas')

    symbol_normalized = ticker_symbol.upper()
    market_for_crypto = "USD" # Default market for crypto
    is_crypto = False
    symbol_to_fetch = symbol_normalized # Default to the full normalized symbol

    # Revised crypto detection logic
    common_crypto_bases = ["BTC", "ETH", "ADA", "SOL", "XRP", "DOGE", "LTC", "BCH", "LINK", "DOT", "UNI"] # Add more common ones
    
    parts = symbol_normalized.split('-')
    if len(parts) == 2:
        base_candidate = parts[0]
        market_candidate = parts[1]
        # Check if base is a known crypto and market is a typical 3-char fiat/crypto code
        if base_candidate in common_crypto_bases and len(market_candidate) == 3:
            is_crypto = True
            symbol_to_fetch = base_candidate
            market_for_crypto = market_candidate
        # Could also be Crypto-Crypto like ETH-BTC
        elif base_candidate in common_crypto_bases and market_candidate in common_crypto_bases:
            is_crypto = True
            symbol_to_fetch = base_candidate
            market_for_crypto = market_candidate # e.g. fetch ETH priced in BTC
    elif symbol_normalized in common_crypto_bases: # Single symbol like "BTC"
        is_crypto = True
        symbol_to_fetch = symbol_normalized
        # market_for_crypto remains "USD" by default

    # Map our interval to Alpha Vantage's interval strings
    av_interval = None
    fetch_function_type = None # E.g., 'intraday', 'daily', 'crypto_daily', 'crypto_intraday'
    
    # Alpha Vantage outputsize: 'compact' (100 points) or 'full' (all available)
    # For daily, 'full' often requires premium. For intraday, 'full' gives more history but still limited by AV.
    outputsize = 'full' # Default to full, will adjust if needed or if it hits premium wall for daily.
    
    interval_lower = interval.lower()
    if interval_lower in ["1m", "1min"]: av_interval = '1min'
    elif interval_lower in ["5m", "5min"]: av_interval = '5min'
    elif interval_lower in ["15m", "15min"]: av_interval = '15min'
    elif interval_lower in ["30m", "30min"]: av_interval = '30min'
    elif interval_lower in ["1h", "60m", "60min", "1hour"]: av_interval = '60min'
    elif interval_lower in ["1d", "1day", "daily"]:
        fetch_function_type = 'daily' if not is_crypto else 'crypto_daily'
        # For daily equity, 'full' might be premium. 'compact' is safer for free tier.
        if not is_crypto: outputsize = 'compact' if days_history <= 100 else 'full' # try full for more if user asks
    else:
        error_message = f"Interval '{interval}' not directly supported or mapped for Alpha Vantage."
        print(error_message)
        return [], [], None, error_message

    if av_interval: # This implies an intraday interval
        fetch_function_type = 'intraday' if not is_crypto else 'crypto_intraday'
        if days_history > 7 : # Heuristic for intraday full outputsize. Still AV limited.
            outputsize = 'full'
        else:
            outputsize = 'compact'


    if not fetch_function_type:
        error_message = f"Could not determine fetch_function_type for {ticker_symbol} with interval {interval}."
        print(error_message)
        return [], [], None, error_message

    try:
        # For crypto intraday, Alpha Vantage TIME_SERIES_INTRADAY endpoint expects the symbol to be concatenated
        # e.g., BTCUSD, ETHEUR. The TimeSeries object handles this if we pass the stock symbol.
        # The market parameter is not directly used by ts.get_intraday(), but it helps us construct the symbol.
        symbol_for_ts_intraday_crypto = symbol_to_fetch 
        if fetch_function_type == 'crypto_intraday':
            symbol_for_ts_intraday_crypto = symbol_to_fetch + market_for_crypto # e.g. BTC + USD -> BTCUSD
            print(f"Adjusted symbol for crypto intraday to: {symbol_for_ts_intraday_crypto}")

        print(f"Alpha Vantage: original_symbol='{ticker_symbol}', fetch_symbol='{symbol_to_fetch if fetch_function_type != 'crypto_intraday' else symbol_for_ts_intraday_crypto}', market_crypto='{market_for_crypto if is_crypto else 'N/A'}', type='{fetch_function_type}', av_interval='{av_interval or 'N/A'}', outputsize='{outputsize}'")
        
        api_call_successful = False
        for attempt in range(3): # Retry loop
            try:
                if fetch_function_type == 'intraday': # Equity Intraday
                    raw_df, meta_data = await asyncio.to_thread(ts.get_intraday, symbol=symbol_to_fetch, interval=av_interval, outputsize=outputsize)
                    api_call_successful = True; break
                elif fetch_function_type == 'crypto_intraday': # Crypto Intraday - use TimeSeries.get_intraday with combined symbol
                    raw_df, meta_data = await asyncio.to_thread(ts.get_intraday, symbol=symbol_for_ts_intraday_crypto, interval=av_interval, outputsize=outputsize)
                    api_call_successful = True; break
                elif fetch_function_type == 'daily': # Equity Daily
                    raw_df, meta_data = await asyncio.to_thread(ts.get_daily, symbol=symbol_to_fetch, outputsize=outputsize)
                    api_call_successful = True; break
                elif fetch_function_type == 'crypto_daily': # Crypto Daily
                    raw_df, meta_data = await asyncio.to_thread(cc.get_digital_currency_daily, symbol=symbol_to_fetch, market=market_for_crypto)
                    api_call_successful = True; break
                else:
                    error_message = f"Unknown fetch_function_type: {fetch_function_type}"
                    break # Break retry loop, api_call_successful will be false
            except ValueError as ve: # Catch errors from alpha_vantage library (e.g. API limits, premium endpoint)
                if "premium endpoint" in str(ve).lower():
                    if fetch_function_type == 'daily' and outputsize == 'full' and not is_crypto: # Equity daily full
                        print(f"Premium endpoint hit for daily equity with outputsize=full. Trying outputsize=compact for {symbol_to_fetch}")
                        outputsize = 'compact' 
                        print(f"Alpha Vantage (retrying equity daily): symbol='{symbol_to_fetch}', type='{fetch_function_type}', outputsize='{outputsize}'")
                        await asyncio.sleep(13) 
                        continue 
                    elif fetch_function_type == 'crypto_intraday':
                         print(f"Premium endpoint hit for crypto_intraday for {symbol_for_ts_intraday_crypto}. Falling back to crypto_daily.")
                         fetch_function_type = 'crypto_daily' 
                         av_interval = None 
                         outputsize = 'full' if days_history > 100 else 'compact'
                         # Update the print statement to reflect the fallback
                         print(f"Alpha Vantage (fallback to crypto_daily): original_symbol='{ticker_symbol}', fetch_symbol='{symbol_to_fetch}', market_crypto='{market_for_crypto}', type='{fetch_function_type}', outputsize='{outputsize}'")
                         await asyncio.sleep(13)
                         continue 
                    else: 
                        error_message = f"Alpha Vantage API error (premium) for {ticker_symbol}: {str(ve)}"
                        break 
                elif "call frequency" in str(ve).lower() or "api key" in str(ve).lower() or "invalid api call" in str(ve).lower():
                    # Check if it's an invalid symbol for intraday crypto
                    if fetch_function_type == 'crypto_intraday' and ("invalid api call" in str(ve).lower() or "symbol" in str(ve).lower()):
                        print(f"Invalid API call for crypto_intraday {symbol_for_ts_intraday_crypto}. Trying fallback to crypto_daily.")
                        fetch_function_type = 'crypto_daily'
                        av_interval = None
                        outputsize = 'full' if days_history > 100 else 'compact'
                        print(f"Alpha Vantage (fallback to crypto_daily due to invalid call): original_symbol='{ticker_symbol}', fetch_symbol='{symbol_to_fetch}', market_crypto='{market_for_crypto}', type='{fetch_function_type}', outputsize='{outputsize}'")
                        await asyncio.sleep(13)
                        continue # Retry with crypto_daily
                    error_message = f"Alpha Vantage API error (freq/key/invalid) for {ticker_symbol}: {str(ve)}"
                    break 
                else: 
                    error_message = f"Alpha Vantage data error for {ticker_symbol}: {str(ve)}"
                    break 
            except Exception as e_generic: # Other unexpected errors
                 error_message = f"Unexpected error fetching from Alpha Vantage for {ticker_symbol}: {str(e_generic)}"
                 break # Break retry loop

            # If an attempt did not result in api_call_successful = True and did not set error_message (e.g. non-ValueError exception not caught above)
            # or if it was a recoverable error and we are about to retry.
            if not api_call_successful and not error_message: # Should not happen if all exceptions are caught
                print(f"Alpha Vantage API call failed or was rate-limited for {ticker_symbol} (Attempt {attempt + 1}/3). Retrying in 15s...")
                await asyncio.sleep(15)
       
        if not api_call_successful and not error_message:
             error_message = f"Failed to fetch data from Alpha Vantage for {ticker_symbol} after retries."

        if error_message:
            print(error_message)
            return [], [], None, error_message

        # Sort by date (index) ascending, as AV often returns descending
        raw_df.sort_index(ascending=True, inplace=True)

        # Filter by days_history.
        if not raw_df.empty:
            # Ensure index is datetime
            if not isinstance(raw_df.index, pd.DatetimeIndex):
                raw_df.index = pd.to_datetime(raw_df.index)
            
            # Make index timezone-naive for comparison if it's timezone-aware
            # Alpha Vantage usually returns timezone-naive timestamps.
            # If it were aware, and we wanted to compare to a naive datetime.now(), convert index first.
            # if raw_df.index.tz is not None:
            #     raw_df.index = raw_df.index.tz_localize(None) # Or .tz_convert('UTC').tz_localize(None)

            cutoff_date = datetime.now() - timedelta(days=days_history)
            raw_df = raw_df[raw_df.index >= cutoff_date].copy() # Add .copy() here

        if raw_df.empty:
            error_message = f"No data returned from Alpha Vantage for {ticker_symbol} in the last {days_history} days (or symbol/interval is invalid)."
            print(error_message)
            return [], [], None, error_message

        print(f"Successfully fetched {len(raw_df)} data points from Alpha Vantage for {ticker_symbol}.")

        # Rename Alpha Vantage columns
        # ts.get_daily() columns: 1. open, 2. high, 3. low, 4. close, 5. volume
        # ts.get_intraday() columns: 1. open, 2. high, 3. low, 4. close, 5. volume
        # cc.get_digital_currency_daily() columns: e.g., '1a. open (USD)', '2a. high (USD)', ..., '5. volume'
        # cc.get_crypto_intraday() columns: e.g., '1. open', '2. high', ..., '5. volume' (market specified in call)
        rename_map = {}
        for col in raw_df.columns:
            col_lower = col.lower()
            if '1. open' in col_lower or '1a. open' in col_lower: rename_map[col] = 'open'
            elif '2. high' in col_lower or '2a. high' in col_lower: rename_map[col] = 'high'
            elif '3. low' in col_lower or '3a. low' in col_lower or '3b. low' in col_lower: rename_map[col] = 'low' # 3a/3b for crypto
            elif '4. close' in col_lower or '4a. close' in col_lower: rename_map[col] = 'close'
            elif '5. volume' in col_lower: rename_map[col] = 'volume'
            # Adjusted close is not typically in get_daily(), but if other functions return it:
            elif 'adjusted close' in col_lower and 'volume' not in raw_df.columns and not any('volume' in c for c in rename_map.values()):
                print(f"Warning: Using 'adjusted close' as 'close' for {ticker_symbol} from AlphaVantage. 'volume' might be missing or taken from another column.")
                if 'close' not in rename_map.values() and not any('close' in c.lower() for c in raw_df.columns if '4.' in c or '4a.' in c):
                     rename_map[col] = 'close'


        raw_df.rename(columns=rename_map, inplace=True)
        
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in raw_df.columns:
                if col == 'volume':
                    print(f"Warning: 'volume' column missing for {ticker_symbol} after rename. Filling with 0.")
                    raw_df['volume'] = 0.0
                else: # Missing essential OHLC column
                    error_message = f"Missing critical column '{col}' for {ticker_symbol} after Alpha Vantage processing. Available: {raw_df.columns.tolist()}"
                    print(error_message)
                    return [], [], raw_df if not raw_df.empty else None, error_message 
        
        for col in required_cols:
            raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce')
        
        raw_df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True) 
        raw_df['volume'] = raw_df['volume'].fillna(0)

        for timestamp_val, row in raw_df.iterrows():
            time_unix = int(pd.Timestamp(timestamp_val).timestamp())
            ohlc_js_list.append({
                "time": time_unix, "open": row['open'], "high": row['high'],
                "low": row['low'], "close": row['close']
            })
            volume_color = 'rgba(0, 150, 136, 0.6)' if row['close'] >= row['open'] else 'rgba(255, 82, 82, 0.6)'
            volume_js_list.append({"time": time_unix, "value": row['volume'], "color": volume_color})
        
        print(f"Formatted {len(ohlc_js_list)} data points for Lightweight Charts for {ticker_symbol} (Alpha Vantage).")
        return ohlc_js_list, volume_js_list, raw_df, None

    except Exception as e:
        error_message = f"Outer error processing Alpha Vantage data for {ticker_symbol}: {str(e)}"
        print(error_message)
        import traceback
        traceback.print_exc()
        return [], [], None, error_message

async def main_test():
    print("--- Testing Alpha Vantage Data Fetcher (Revised for Crypto Intraday & .env loading) ---")
    
    test_symbols = [
        {"ticker": "IBM", "days": 30, "interval": "60min"},     # Equity intraday
        {"ticker": "BTC-USD", "days": 7, "interval": "15min"}, # Crypto intraday (BTCUSD) - may fallback to daily
        # {"ticker": "MSFT", "days": 100, "interval": "daily"},    
        # {"ticker": "AAPL", "days": 250, "interval": "daily"},    
        # {"ticker": "GOOG", "days": 5, "interval": "15min"},      
        # {"ticker": "BTC-USD", "days": 60, "interval": "daily"},  
        # {"ticker": "ETH-EUR", "days": 30, "interval": "daily"},  
        # {"ticker": "SOL-USD", "days": 7, "interval": "60min"}, 
        # {"ticker": "ETH-BTC", "days": 7, "interval": "1h"},    
        {"ticker": "NONEXISTENTXYZ", "days": 5, "interval": "daily"} 
    ]

    for test_case in test_symbols:
        symbol, days, interval = test_case["ticker"], test_case["days"], test_case["interval"]
        print(f"\n>>> Testing: {symbol} ({days} days, {interval} interval)")
        await asyncio.sleep(15) # Wait 15 seconds between *top-level* API calls to respect 5 calls/min limit
        
        ohlc_list, volume_list, df_raw, error = await get_ohlcv_data(symbol, days_history=days, interval=interval)
        
        if error:
            print(f"Error for {symbol} ({interval}): {error}")
        else:
            print(f"SUCCESS for {symbol} ({interval}).")
            print(f"OHLC samples (first 2): {ohlc_list[:2]}")
            # print(f"Volume samples (first 2): {volume_list[:2]}")
            if df_raw is not None and not df_raw.empty:
                print(f"Raw DataFrame shape: {df_raw.shape}")
                print(f"Raw DataFrame head:\n{df_raw.head()}")
                if not isinstance(df_raw.index, pd.DatetimeIndex):
                     print(f"WARNING: Raw DF for {symbol} index is not DatetimeIndex. Type: {type(df_raw.index)}")
            elif df_raw is not None and df_raw.empty:
                 print(f"{symbol} Raw DataFrame is empty (function might have reported an error string too).")

if __name__ == "__main__":
    asyncio.run(main_test())