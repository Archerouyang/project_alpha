# backend/core/chart_generator.py
import asyncio
import os
import pandas as pd
import pandas_ta as ta
from datetime import datetime, date
from typing import Optional, Tuple, List, Dict, Any

from playwright.async_api import async_playwright

class ChartGenerator:
    def __init__(self, output_dir: str = "generated_reports"):
        self.output_dir = output_dir
        # Resolve the path to the template relative to this script's location
        self.template_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', 'templates', 'chart_template.html'
        ))
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Chart template not found at {self.template_path}")
        print(f"ChartGenerator initialized. Template: {self.template_path}, Output: {self.output_dir}")

    def _format_data_for_js(self, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Formats the DataFrame for the Lightweight Charts library."""
        ohlc_data = []
        volume_data = []
        stoch_k_data = []
        stoch_d_data = []

        # Ensure required columns exist, handling potential case differences
        df.columns = [col.lower() for col in df.columns]
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in DataFrame.")
        
        # Check if indicator columns exist before processing
        has_stoch = 'stochk_14_3_3' in df.columns and 'stochd_14_3_3' in df.columns

        for timestamp, row in df.iterrows():
            # Convert date to datetime if necessary before getting timestamp
            if isinstance(timestamp, date) and not isinstance(timestamp, datetime):
                # For date objects, combine with midnight time to create datetime
                timestamp = datetime.combine(timestamp, datetime.min.time())
            
            time_unix = int(timestamp.timestamp())
            
            # OHLC and Volume data
            ohlc_data.append({
                "time": time_unix,
                "open": row['open'],
                "high": row['high'],
                "low": row['low'],
                "close": row['close']
            })
            volume_color = 'rgba(0, 150, 136, 0.6)' if row['close'] >= row['open'] else 'rgba(255, 82, 82, 0.6)'
            volume_data.append({"time": time_unix, "value": row['volume'], "color": volume_color})
            
            # Stochastic RSI data
            if has_stoch and pd.notna(row['stochk_14_3_3']) and pd.notna(row['stochd_14_3_3']):
                stoch_k_data.append({"time": time_unix, "value": row['stochk_14_3_3']})
                stoch_d_data.append({"time": time_unix, "value": row['stochd_14_3_3']})
        
        print(f"Formatted OHLC data points: {len(ohlc_data)}")
        print(f"Formatted Volume data points: {len(volume_data)}")
        print(f"Formatted Stoch K data points: {len(stoch_k_data)}")
        print(f"Formatted Stoch D data points: {len(stoch_d_data)}")
        
        return ohlc_data, volume_data, stoch_k_data, stoch_d_data

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates and appends Bollinger Bands and StochRSI indicators."""
        print(f"Calculating indicators on {len(df)} points...")
        df_copy = df.copy() # Work on a copy to avoid side effects
        try:
            # Calculate Bollinger Bands
            df_copy.ta.bbands(length=20, std=2, append=True)
            
            # Calculate Stochastic RSI
            df_copy.ta.stochrsi(length=14, rsi_length=14, k=3, d=3, append=True)
            
            # Rename columns for clarity and consistency
            rename_map = {
                'BBL_20_2.0': 'bbl', # Lower Band
                'BBM_20_2.0': 'bbm', # Middle Band
                'BBU_20_2.0': 'bbu', # Upper Band
                'STOCHRSIk_14_14_3_3': 'stochk_14_3_3',
                'STOCHRSId_14_14_3_3': 'stochd_14_3_3'
            }
            df_copy.rename(columns=lambda c: rename_map.get(c, c), inplace=True)
            
            # Safely check for calculated columns before printing counts
            bband_count = df_copy['bbm'].count() if 'bbm' in df_copy.columns else 0
            stoch_count = df_copy['stochk_14_3_3'].count() if 'stochk_14_3_3' in df_copy.columns else 0
            print(f"Indicators calculated. Bollinger Bands points: {bband_count}, StochRSI_K points: {stoch_count}")

        except Exception as e:
            print(f"Error calculating indicators: {e}")
        return df_copy # Return the modified copy

    def _get_indicator_data_for_js(self, df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
        """Extracts indicator data into a format for JavaScript."""
        indicator_data = {}
        
        # Helper function to convert date to datetime if needed
        def get_timestamp(dt_obj):
            if isinstance(dt_obj, date) and not isinstance(dt_obj, datetime):
                return int(datetime.combine(dt_obj, datetime.min.time()).timestamp())
            return int(dt_obj.timestamp())

        # Extract Bollinger Bands data
        for band in ['bbu', 'bbm', 'bbl']:
            if band in df.columns:
                band_df = df[[band]].dropna().reset_index()
                indicator_data[band] = band_df.apply(
                    lambda row: {'time': get_timestamp(row['date']), 'value': row[band]}, axis=1
                ).tolist()

        print(f"Formatted BBU data points: {len(indicator_data.get('bbu', []))}")
        print(f"Formatted BBM data points: {len(indicator_data.get('bbm', []))}")
        print(f"Formatted BBL data points: {len(indicator_data.get('bbl', []))}")
        
        return indicator_data

    async def generate_chart_from_df(self, raw_df: pd.DataFrame, ticker_symbol: str, interval: str) -> Optional[bytes]:
        """
        Generates a chart image from a given pandas DataFrame and returns the image bytes.
        """
        # 1. Calculate indicators
        df_with_indicators = self._calculate_indicators(raw_df)

        # 2. Format all data for JavaScript
        ohlc_data, volume_data, stoch_k_data, stoch_d_data = self._format_data_for_js(df_with_indicators)
        indicator_data = self._get_indicator_data_for_js(df_with_indicators)
        
        # 3. Create the chart using Playwright
        print(f"Playwright: Launching browser for {ticker_symbol}...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()

                # Add a listener for console messages
                page.on("console", lambda msg: print(f"Browser Console ({msg.type}): {msg.text}"))

                template_url = f"file://{self.template_path}"
                print(f"Playwright: Loaded HTML template: {template_url}")
                await page.goto(template_url)
                
                await page.wait_for_function("typeof window.renderChart === 'function'")

                # Call the JavaScript function to render the chart
                # Ensure the data passed matches the structure expected by the JS function
                await page.evaluate("""
                    (args) => window.renderChart(args)
                """, {
                    "ohlcData": ohlc_data,
                    "volumeData": volume_data,
                    "stochKData": stoch_k_data,
                    "stochDData": stoch_d_data,
                    "bbuData": indicator_data.get('bbu', []),
                    "bbmData": indicator_data.get('bbm', []),
                    "bblData": indicator_data.get('bbl', []),
                    "tickerSymbol": ticker_symbol.upper(),
                    "interval": interval,
                    "chartWidth": 1280,
                    "chartHeight": 720
                })
                print(f"Playwright: Chart rendering initiated for {ticker_symbol} via JS call.")

                # Give the chart a moment to render before taking a screenshot
                await page.wait_for_timeout(2000)
                print(f"Playwright: Waited for rendering for {ticker_symbol}.")

                # Take a screenshot of the chart container element
                chart_element = await page.query_selector('#chart-container-wrapper')
                if not chart_element:
                    raise RuntimeError("Could not find '#chart-container-wrapper' element in the HTML template.")
                
                image_bytes = await chart_element.screenshot()
                print(f"Playwright: Screenshot captured as bytes for {ticker_symbol}.")
                
                await browser.close()
                print(f"Playwright: Browser closed for {ticker_symbol}.")

                return image_bytes
                
        except Exception as e:
            print(f"An error occurred during chart generation for {ticker_symbol}: {e}")
            # Reraise to see full traceback in orchestrator
            raise

# Example Usage (Updated):
async def main():
    """
    An example of how to use the ChartGenerator.
    This will fetch data and then generate a chart image file.
    """
    print("--- Testing ChartGenerator ---")
    
    # 1. Import the data fetcher
    # Placed here to avoid circular dependency issues if chart_generator is imported elsewhere
    from backend.core.data_fetcher import get_ohlcv_data

    # 2. Setup generator and test case
    generator = ChartGenerator(output_dir="generated_reports")
    ticker = "TSLA"
    days = 30
    interval = "1h"

    print(f"\n--- Generating chart for {ticker} ({interval} for {days} days) ---")

    # 3. Fetch data
    # We get back both the formatted data for JS and the raw df for indicator calculation
    js_data, raw_df = await get_ohlcv_data(ticker, days, interval)

    if raw_df is None or raw_df.empty:
        print(f"Could not fetch data for {ticker}. Aborting chart generation.")
        return

    # 4. Generate chart image from the raw DataFrame
    image_bytes = await generator.generate_chart_from_df(
        raw_df=raw_df, 
        ticker_symbol=ticker,
        interval=interval
    )

    # 5. Save the image to a file
    if image_bytes:
        if not os.path.exists(generator.output_dir):
            os.makedirs(generator.output_dir)
        
        # Sanitize ticker for filename
        safe_ticker = ticker.replace("/", "_").replace(":", "_")
        filename = f"{safe_ticker}_{interval}_{days}d_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(generator.output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        print(f"Chart for {ticker} saved successfully to: {filepath}")
    else:
        print(f"FAILED to generate chart image bytes for {ticker}.")


if __name__ == "__main__":
    # Ensure the event loop is managed correctly
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred in the main execution: {e}")
        import traceback
        traceback.print_exc()