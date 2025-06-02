# backend/core/data_fetcher.py
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import Tuple, List, Optional, Dict, Any
import httpx # For potential direct API call fallback
from openbb import obb
from alpha_vantage.timeseries import TimeSeries # For Alpha Vantage fallback
from config.settings import settings # For ALPHA_VANTAGE_API_KEY

# Use the API key from settings
# ALPHA_VANTAGE_API_KEY = "MZOOXS1S8TXQNOA8" # This will be removed

# --- Placeholder for Direct Binance API Call ---
async def fetch_binance_ohlcv_direct(symbol: str, interval: str, limit: int) -> Optional[pd.DataFrame]:
    """
    Placeholder: Fetches OHLCV data directly from Binance public API.
    Binance API intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    Symbol format: BTCUSDT (no slashes or hyphens)
    Limit: Number of data points, max 1000.
    """
    print(f"[Placeholder] Attempting to fetch {symbol} directly from Binance API, interval {interval}, limit {limit}.")
    # Sanitize symbol for Binance: e.g., BTC/USDT -> BTCUSDT, BTC-USD -> BTCUSDT
    binance_symbol = symbol.replace('/', '').replace('-', '').upper()
    
    # Map interval to Binance format (this is a simplified example)
    interval_map = {
        "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "4h": "4h", "1d": "1d" 
    }
    binance_interval = interval_map.get(interval.lower())
    if not binance_interval:
        print(f"[Placeholder Binance Direct] Interval {interval} not supported by this simplified direct fetcher.")
        return None

    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": binance_symbol,
        "interval": binance_interval,
        "limit": limit
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params)
            response.raise_for_status() # Raise an exception for HTTP errors
            data = response.json()
            
            # Convert to Pandas DataFrame
            # Binance klines format: [open_time, open, high, low, close, volume, close_time, quote_asset_volume, 
            #                       number_of_trades, taker_buy_base_asset_volume, taker_buy_quote_asset_volume, ignore]
            df = pd.DataFrame(data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 
                'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 
                'taker_buy_quote_asset_volume', 'ignore'
            ])
            df['date'] = pd.to_datetime(df['open_time'], unit='ms')
            df.set_index('date', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            print(f"[Placeholder Binance Direct] Successfully fetched {len(df)} points for {binance_symbol}.")
            return df
    except httpx.HTTPStatusError as e:
        print(f"[Placeholder Binance Direct] HTTP error for {binance_symbol}: {e} - Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"[Placeholder Binance Direct] Error fetching {binance_symbol}: {e}")
        return None
# --- End Placeholder ---

# --- Helper for Alpha Vantage Equity Fallback ---
async def fetch_equity_alpha_vantage(ticker_symbol: str, days_history: int, interval_str: str) -> Optional[pd.DataFrame]:
    print(f"Attempting Alpha Vantage fallback for {ticker_symbol}, interval {interval_str}")
    if not settings.ALPHA_VANTAGE_API_KEY:
        print("ALPHA_VANTAGE_API_KEY not configured for fallback.")
        return None

    ts = TimeSeries(key=settings.ALPHA_VANTAGE_API_KEY, output_format='pandas')
    av_interval_map = {"1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min", "1h": "60min", "60min":"60min"} # AV uses 'min'
    av_interval = av_interval_map.get(interval_str.lower())
    outputsize = 'full' if days_history > 7 else 'compact' # Simple heuristic for AV

    try:
        if av_interval: # Intraday
            data, _ = await asyncio.to_thread(ts.get_intraday, symbol=ticker_symbol, interval=av_interval, outputsize=outputsize)
        else: # Daily (if interval is '1d' or not in map)
            data, _ = await asyncio.to_thread(ts.get_daily, symbol=ticker_symbol, outputsize=outputsize)
        
        data.rename(columns={
            '1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close', '5. volume': 'volume',
            '1a. open (USD)': 'open', '2a. high (USD)': 'high', '3a. low (USD)': 'low', '4a. close (USD)': 'close', # For crypto via AV if ever used
        }, inplace=True)
        
        # Ensure essential columns exist and are numeric
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                if col == 'volume': data['volume'] = 0.0
                else: raise ValueError(f"Missing critical column {col} from Alpha Vantage for {ticker_symbol}")
        for col in required_cols: data[col] = pd.to_numeric(data[col], errors='coerce')

        data.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
        data['volume'] = data['volume'].fillna(0)
        data.sort_index(ascending=True, inplace=True)
        
        # Filter by days_history more precisely
        if not data.empty:
            cutoff_date = datetime.now() - timedelta(days=days_history)
            data = data[data.index >= cutoff_date]

        print(f"Alpha Vantage fallback successful for {ticker_symbol}, {len(data)} points.")
        return data if not data.empty else None
    except Exception as e:
        print(f"Alpha Vantage fallback failed for {ticker_symbol}: {e}")
        return None

def map_interval_to_openbb(interval_str: str) -> str:
    """Maps common interval strings to OpenBB's expected 'interval' enum where possible.
       OpenBB intervals: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo
    """
    interval_lower = interval_str.lower()
    # Direct maps for OpenBB's common intervals
    if interval_lower in ["1m", "1min"]: return "1m"
    if interval_lower in ["5m", "5min"]: return "5m"
    if interval_lower in ["15m", "15min"]: return "15m"
    if interval_lower in ["30m", "30min"]: return "30m"
    if interval_lower in ["1h", "60m", "60min", "1hour"]: return "1h"
    if interval_lower in ["4h", "240m", "4hour"]: return "4h"
    if interval_lower in ["1d", "1day", "daily"]: return "1d"
    if interval_lower in ["1w", "1wk", "1week", "weekly"]: return "1w"
    if interval_lower in ["1mo", "1month", "monthly"]: return "1mo"
    
    print(f"Warning: Interval '{interval_str}' not directly mapped to OpenBB interval. Using as is or defaulting (e.g., '1d').")
    # Fallback or attempt to use directly if OpenBB provider is flexible
    return interval_str # Or a default like "1d" if strict mapping is needed

async def get_ohlcv_data(
    ticker_symbol: str,
    days_history: int = 365, # Default to more history for OpenBB
    interval: str = "1d"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Optional[pd.DataFrame], Optional[str]]:
    """
    Fetches historical OHLCV data using OpenBB SDK, prioritizing free sources.
    Formats it for Lightweight Charts and returns the raw DataFrame.

    Args:
        ticker_symbol (str): The stock/crypto symbol (e.g., "AAPL", "BTC/USDT", "ETH-USD").
        days_history (int): Number of past days to fetch data for.
        interval (str): Data interval (e.g., "1m", "15m", "1h", "4h", "1d").

    Returns:
        tuple[list, list, pd.DataFrame | None, str | None]:
            - List of dicts for OHLC data: {time, open, high, low, close}
            - List of dicts for Volume data: {time, value, color}
            - Raw pandas DataFrame with DatetimeIndex and ohlcv columns (lowercase), or None on error.
            - Error message string if an error occurs, otherwise None.
    """
    print(f"Fetching data for '{ticker_symbol}' using OpenBB SDK: {days_history} days, interval '{interval}'...")
    error_message = None
    raw_df = pd.DataFrame()
    ohlc_js_list = []
    volume_js_list = []

    start_date = (datetime.now() - timedelta(days=days_history)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    openbb_interval = map_interval_to_openbb(interval)

    try:
        is_crypto = False
        common_crypto_bases = ["BTC", "ETH", "ADA", "SOL", "XRP", "DOGE", "LTC", "BCH", "LINK", "DOT", "UNI"]
        symbol_parts = ticker_symbol.upper().replace('-', '/').split('/')
        base_symbol_candidate = symbol_parts[0]

        if base_symbol_candidate in common_crypto_bases or any(c in ticker_symbol.upper() for c in ["/", "-USD", "-USDT", "-BTC", "-ETH"]):
            is_crypto = True
            if base_symbol_candidate == ticker_symbol.upper(): # e.g. user typed "BTC"
                 print(f"Assuming '{ticker_symbol}/USD' for crypto if only base is provided.")
                 base_symbol_candidate = ticker_symbol.upper()
                 # symbol_parts might need update if we reconstruct ticker_symbol
                 ticker_symbol = f"{base_symbol_candidate}/USD" 
                 symbol_parts = [base_symbol_candidate, "USD"]

        if not is_crypto:
            print(f"Attempting to fetch '{ticker_symbol}' as equity.")
            if settings.FMP_API_KEY:
                print("Attempting OpenBB (FMP provider) for equity.")
                try:
                    equity_data_obb_fmp = await asyncio.to_thread(
                        obb.equity.price.historical,
                        symbol=ticker_symbol,
                        start_date=start_date,
                        end_date=end_date,
                        interval=openbb_interval,
                        provider="fmp"
                    )
                    if equity_data_obb_fmp and hasattr(equity_data_obb_fmp, 'to_dataframe') and not equity_data_obb_fmp.to_dataframe().empty:
                        raw_df = equity_data_obb_fmp.to_dataframe()
                        print(f"Successfully fetched equity data for '{ticker_symbol}' via OpenBB/FMP.")
                        error_message = None # Successful fetch
                    else:
                        # FMP provider returned no data, or empty dataframe
                        error_message = f"OpenBB/FMP returned no data for equity '{ticker_symbol}'."
                        # raw_df will remain empty
                except Exception as e_equity_fmp:
                    error_message = f"OpenBB/FMP fetch for equity '{ticker_symbol}' failed: {type(e_equity_fmp).__name__}: {e_equity_fmp}"
                    # raw_df will remain empty
            else: # FMP_API_KEY is not set
                error_message = f"FMP_API_KEY not configured. Cannot fetch equity data for '{ticker_symbol}' via FMP."
                print(error_message)
            
            # If FMP was attempted (or skipped due to no key) and raw_df is still empty,
            # 'error_message' is now set. No further equity provider fallbacks are attempted.
            # The general error check later in the function will use this 'error_message'.

        if is_crypto:
            print(f"Attempting to fetch '{ticker_symbol}' as crypto using OpenBB (yfinance provider).")
            # For OpenBB crypto with yfinance, symbol format is often like "BTC-USD"
            crypto_symbol_yf_format = base_symbol_candidate
            quote_currency = "USD" # yfinance usually pairs with USD
            if len(symbol_parts) > 1:
                quote_currency = symbol_parts[1]
            crypto_symbol_yf_format = f"{base_symbol_candidate}-{quote_currency.upper()}"
            
            print(f"OpenBB Crypto: Symbol='{crypto_symbol_yf_format}', Interval='{openbb_interval}', Provider='yfinance'")
            try:
                # Note: obb.crypto.price.historical with yfinance provider.
                # The 'symbol' and 'to_symbol' params might not be used by yfinance provider directly if symbol is already "BTC-USD"
                # We will pass the combined symbol to the 'symbol' parameter for yfinance provider.
                
                # Before making the call, ensure OpenBB credentials for FMP are set if needed for any global config
                # This is more of a general OpenBB setup if a specific provider needs it.
                # However, for crypto with yfinance, FMP key is not relevant.
                
                crypto_data_obb = await asyncio.to_thread(
                    obb.crypto.price.historical,
                    symbol=crypto_symbol_yf_format, 
                    start_date=start_date,
                    end_date=end_date,
                    interval=openbb_interval,
                    provider="yfinance" # Using yfinance as the provider
                )
                if crypto_data_obb and hasattr(crypto_data_obb, 'to_dataframe') and not crypto_data_obb.to_dataframe().empty:
                    raw_df = crypto_data_obb.to_dataframe()
                    print(f"Successfully fetched crypto data for '{crypto_symbol_yf_format}' via OpenBB/yfinance.")
                else:
                    raise ValueError(f"OpenBB/yfinance returned no crypto data for {crypto_symbol_yf_format}.")
            except Exception as e_crypto_obb_yf:
                print(f"OpenBB/yfinance fetch for crypto '{crypto_symbol_yf_format}' failed: {type(e_crypto_obb_yf).__name__}: {e_crypto_obb_yf}")
                error_message = f"OpenBB/yfinance fetch failed for crypto '{crypto_symbol_yf_format}'."
                # Consider direct Binance fallback if applicable and symbol was Binance-like, though yfinance might not be binance.
                if "binance" in ticker_symbol.lower() or "USDT" in ticker_symbol.upper(): # Heuristic
                    print(f"Attempting direct Binance API fallback for '{ticker_symbol}' due to OpenBB/yfinance crypto failure.")
                    limit_approx = min(days_history * 24 if 'h' in interval else days_history, 1000)
                    direct_df = await fetch_binance_ohlcv_direct(ticker_symbol, interval, limit_approx)
                    if direct_df is not None and not direct_df.empty:
                        raw_df = direct_df
                        error_message = None # Succeeded with direct
                        print(f"Successfully fetched data for '{ticker_symbol}' using direct Binance API call.")
                    else:
                         error_message += " Direct Binance API fallback also failed." # Append to existing error

        if error_message and raw_df.empty:
            print(error_message)
            return [], [], None, error_message
        
        if raw_df.empty:
            error_message = f"No data successfully fetched for '{ticker_symbol}' after all attempts."
            print(error_message)
            return [], [], None, error_message

        # Common Post-processing 
        raw_df.index.name = 'date'
        if not isinstance(raw_df.index, pd.DatetimeIndex):
            raw_df.index = pd.to_datetime(raw_df.index)
        
        # Standardize column names (OpenBB/yf often returns 'Adj Close')
        rename_map_std = {}
        for col in raw_df.columns:
            col_lower = col.lower()
            if 'open' in col_lower: rename_map_std[col] = 'open'
            elif 'high' in col_lower: rename_map_std[col] = 'high'
            elif 'low' in col_lower: rename_map_std[col] = 'low'
            elif 'close' in col_lower and 'adj' not in col_lower : rename_map_std[col] = 'close' # Prioritize non-adjusted
            elif 'adj close' in col_lower : 
                if 'close' not in rename_map_std.values(): rename_map_std[col] = 'close' # Use adj close if no plain close
            elif 'volume' in col_lower: rename_map_std[col] = 'volume'
        raw_df.rename(columns=rename_map_std, inplace=True)

        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in raw_df.columns:
                if col == 'volume':
                    print(f"Warning: 'volume' column missing for {ticker_symbol}. Filling with 0.")
                    raw_df['volume'] = 0.0
                else:
                    error_message = f"Missing critical column '{col}' for {ticker_symbol}. Available: {raw_df.columns.tolist()}"
                    print(error_message)
                    return [], [], raw_df if not raw_df.empty else None, error_message
        
        for col in required_cols: raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce')
        raw_df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
        raw_df['volume'] = raw_df['volume'].fillna(0)
        raw_df.sort_index(ascending=True, inplace=True)

        if raw_df.empty:
            error_message = f"No data remained for '{ticker_symbol}' after processing."
            print(error_message)
            return [], [], None, error_message

        print(f"Successfully processed {len(raw_df)} data points for '{ticker_symbol}'.")

        for _, row in raw_df.iterrows(): # Iterate using index
            time_unix = int(row.name.timestamp()) # row.name is the timestamp index
            ohlc_js_list.append({"time": time_unix, "open": row['open'], "high": row['high'], "low": row['low'], "close": row['close']})
            volume_color = 'rgba(0, 150, 136, 0.6)' if row['close'] >= row['open'] else 'rgba(255, 82, 82, 0.6)'
            volume_js_list.append({"time": time_unix, "value": row['volume'], "color": volume_color})
        
        print(f"Formatted {len(ohlc_js_list)} data points for Lightweight Charts for '{ticker_symbol}'.")
        return ohlc_js_list, volume_js_list, raw_df, None

    except Exception as e:
        error_message = f"Outer error in get_ohlcv_data for '{ticker_symbol}': {type(e).__name__}: {e}"
        print(error_message)
        import traceback
        traceback.print_exc()
        return [], [], None, error_message

async def main_test():
    print("--- Testing Data Fetcher (FMP > OpenBB/yf > AV Fallback & yf Crypto) ---")
    
    if settings.FMP_API_KEY:
        try:
            print(f"FMP API Key found, attempting to set for OpenBB: {settings.FMP_API_KEY[:5]}...")
            obb.user.credentials.fmp_api_key = settings.FMP_API_KEY
            print("Successfully set obb.user.credentials.fmp_api_key")
        except AttributeError as e:
            print(f"Could not set obb.user.credentials.fmp_api_key directly. Error: {e}")
            print("This might happen if obb.user.credentials structure is different or not yet initialized.")
            print("OpenBB might still pick up the key if OPENBB_FMP_API_KEY env var is set and used by FMP provider.")
        except Exception as e:
            print(f"An unexpected error occurred while setting obb.user.credentials.fmp_api_key: {e}")
    else:
        print("FMP_API_KEY not found in settings, OpenBB/FMP provider will likely fail.")

    test_symbols = [
        {"ticker": "TSLA", "days": 30, "interval": "1h"},    # Equity test
        # {"ticker": "AAPL", "days": 90, "interval": "1d"},     
        # {"ticker": "MSFT", "days": 30, "interval": "1h"},     
        # {"ticker": "BTC-USD", "days": 7, "interval": "15m"}, # Crypto test with yfinance
        # {"ticker": "ETH/USD", "days": 30, "interval": "4h"}, 
        # {"ticker": "NONEXISTENTXYZ", "days": 5, "interval": "1d"},
        # {"ticker": "DOGE-USDT", "days": 5, "interval": "1h"}, # Will likely fail or use direct (geo-blocked)
    ]

    for test_case in test_symbols:
        symbol, days, interval = test_case["ticker"], test_case["days"], test_case["interval"]
        print(f"\n>>> Testing: {symbol} ({days} days, {interval} interval)")
        
        ohlc_list, volume_list, df_raw, error = await get_ohlcv_data(symbol, days_history=days, interval=interval)
        
        if error:
            print(f"Error for {symbol} ({interval}): {error}")
        else:
            print(f"SUCCESS for {symbol} ({interval}).")
            if ohlc_list:
                 print(f"OHLC samples (first 2): {ohlc_list[:2]}")
            else:
                 print(f"OHLC list is empty for {symbol}")
            
            if df_raw is not None and not df_raw.empty:
                print(f"Raw DataFrame shape: {df_raw.shape}")
                print(f"Raw DataFrame head:\n{df_raw.head()}")
            elif df_raw is not None and df_raw.empty:
                 print(f"{symbol} Raw DataFrame is empty.")
            else:
                 print(f"{symbol} Raw DataFrame is None.")
        print("-" * 50)

if __name__ == "__main__":
    # To allow OpenBB to potentially use asyncio features if it expects an existing loop
    # For command line, asyncio.run is fine. If integrating into FastAPI, FastAPI manages the loop.
    asyncio.run(main_test())