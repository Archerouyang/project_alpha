# scripts/generate_chart_cli.py
import argparse
import json
import os
import sys

# Add the project root to the Python path to allow importing from 'backend'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import our modules
from backend.core.chart_generator import ChartGenerator
from backend.core.data_fetcher import get_ohlcv_data

def main():
    """
    This script is a command-line interface for generating a single stock chart image.
    It fetches data, generates a chart, and saves the resulting image and key
    financial data to specified output files. This process is now fully synchronous.
    """
    parser = argparse.ArgumentParser(description="Generate a stock chart image and associated data.")
    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol (e.g., AAPL, BTC-USD).")
    parser.add_argument("--interval", type=str, default="1d", help="Data interval (e.g., 1h, 4h, 1d).")
    parser.add_argument("--num-candles", type=int, default=150, help="Number of candles to display on the chart.")
    parser.add_argument("--exchange", type=str, default=None, help="The crypto exchange to use (e.g., KRAKEN, BINANCE).")
    parser.add_argument("--output-image", type=str, required=True, help="Path to save the output chart image.")
    parser.add_argument("--output-data", type=str, required=True, help="Path to save the output key data JSON file.")
    
    args = parser.parse_args()

    print(f"CLI: Starting chart generation for {args.ticker}...")

    # 1. Fetch data directly, as the function is now synchronous.
    try:
        _, raw_df = get_ohlcv_data(args.ticker, args.interval, args.num_candles, args.exchange)
        if raw_df is None or raw_df.empty:
            raise ValueError(f"No data fetched for ticker {args.ticker}.")
        print(f"CLI: Successfully fetched {len(raw_df)} data points.")
    except Exception as e:
        print(f"CLI: Error fetching data: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Generate the chart image and key data.
    try:
        chart_gen = ChartGenerator()
        image_bytes, key_data = chart_gen.generate_chart_from_df(
            raw_df=raw_df,
            ticker_symbol=args.ticker,
            interval=args.interval
        )
        if not image_bytes or not key_data:
            raise RuntimeError("Chart generation returned empty data.")
        print("CLI: Successfully generated chart image and key data.")
    except Exception as e:
        print(f"CLI: Error during chart generation: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Save the outputs to the specified files.
    try:
        with open(args.output_image, "wb") as f:
            f.write(image_bytes)
        print(f"CLI: Chart image saved to {args.output_image}")

        with open(args.output_data, "w", encoding="utf-8") as f:
            json.dump(key_data, f, ensure_ascii=False, indent=4)
        print(f"CLI: Key data saved to {args.output_data}")

    except Exception as e:
        print(f"CLI: Error saving output files: {e}", file=sys.stderr)
        sys.exit(1)
        
    print("CLI: Chart generation process completed successfully.")

if __name__ == "__main__":
    main() 