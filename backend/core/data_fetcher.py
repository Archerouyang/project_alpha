# backend/core/data_fetcher.py
import yfinance as yf
import pandas as pd

async def get_stock_data(stock_code: str, period: str = "20d", interval: str = "1h") -> pd.DataFrame:
    """
    Fetches historical K-line data for a given stock code.

    Args:
        stock_code (str): The stock symbol (e.g., "AAPL").
        period (str): The period for which to fetch data (e.g., "1mo", "20d").
        interval (str): The data interval (e.g., "1h", "1d").

    Returns:
        pd.DataFrame: A pandas DataFrame with the K-line data (OHLC, Volume),
                      or an empty DataFrame if an error occurs.
    """
    print(f"Fetching data for {stock_code} for period {period} and interval {interval}...")
    try:
        ticker = yf.Ticker(stock_code)
        # Adjusting history call based on typical yfinance usage for K-lines
        # yfinance typically returns OHLCV (Open, High, Low, Close, Volume)
        # It might also include 'Dividends' and 'Stock Splits' if they occurred.
        hist_data = ticker.history(period=period, interval=interval)
        
        if hist_data.empty:
            print(f"No data found for {stock_code} with period {period} and interval {interval}.")
            return pd.DataFrame()

        # Ensure the essential columns are present
        # yfinance columns are typically: Open, High, Low, Close, Volume
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in hist_data.columns for col in required_columns):
            print(f"Data for {stock_code} is missing some required columns (OHLCV).")
            return pd.DataFrame()
            
        print(f"Data fetched successfully for {stock_code}.")
        return hist_data
    except Exception as e:
        print(f"Error fetching data for {stock_code}: {e}")
        return pd.DataFrame()

# Example usage (can be run directly for testing):
# if __name__ == "__main__":
#     import asyncio
#     async def main_test():
#         data = await get_stock_data("AAPL")
#         if not data.empty:
#             print(data.head())
#         else:
#             print("Could not fetch data.")
#     asyncio.run(main_test()) 