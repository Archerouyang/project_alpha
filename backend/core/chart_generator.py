# backend/core/chart_generator.py
import asyncio
import pandas as pd
import pandas_ta as ta
from playwright.async_api import async_playwright
import os
import json
from typing import Optional, Dict, List, Any, Union
from io import BytesIO
from .data_fetcher import get_ohlcv_data # Use the OpenBB data fetcher

class LightweightChartGenerator:
    def __init__(self,
                 template_dir: str = "backend/templates",
                 output_dir: str = "generated_reports",
                 default_chart_width: int = 1280, 
                 default_chart_height: int = 720): # This height is for the wrapper
        self.template_path = os.path.abspath(os.path.join(os.getcwd(), template_dir, "chart_template.html"))
        self.output_dir = os.path.abspath(os.path.join(os.getcwd(), output_dir))
        self.chart_width = default_chart_width
        self.chart_height = default_chart_height 
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"ChartGenerator initialized. Template: {self.template_path}, Output: {self.output_dir}")
        if not os.path.exists(self.template_path):
            print(f"CRITICAL ERROR: Chart template not found at {self.template_path}. Check path.")

    def _format_series_for_js(self, df_series: Optional[pd.Series]) -> List[Dict[str, Any]]:
        """Helper to format a Pandas Series (time-indexed) into {time, value} list for JS."""
        series_data = []
        if df_series is None or df_series.empty:
            return series_data
            
        for timestamp, value in df_series.items():
            if pd.notna(value) and isinstance(timestamp, pd.Timestamp):
                item = {"time": int(timestamp.timestamp()), "value": float(value)}
                series_data.append(item)
        return series_data

    async def generate_chart_image(self, 
                                   ticker_symbol: str, 
                                   days: int = 20, 
                                   interval: str = "1h",
                                   return_bytes: bool = False) -> Union[str, BytesIO, None]:
        print(f"Starting chart generation for {ticker_symbol} ({days}d, {interval}). Plan: EMA(50,200), StochRSI(14,3,3).")
        
        ohlc_js_list, volume_js_list, raw_df, data_error = await get_ohlcv_data(
            ticker_symbol, days_history=days, interval=interval
        )

        if data_error or raw_df is None or raw_df.empty:
            print(f"Error fetching or insufficient data for {ticker_symbol}: {data_error or 'No data returned'}")
            return None
        
        print(f"Data fetched for {ticker_symbol}, calculating indicators on {len(raw_df)} points...")
        df = raw_df.copy()

        # Calculate EMA(50) and EMA(200)
        df['EMA_50'] = df.ta.ema(length=50, close='close', append=False)
        df['EMA_200'] = df.ta.ema(length=200, close='close', append=False)

        # Calculate StochRSI(14, rsi_length=14, k=3, d=3)
        # pandas-ta stochrsi returns two columns: STOCHRSIk_14_14_3_3 and STOCHRSId_14_14_3_3
        stoch_rsi_df = df.ta.stochrsi(length=14, rsi_length=14, k=3, d=3, append=False)
        if stoch_rsi_df is not None and not stoch_rsi_df.empty:
            df['STOCHRSI_K'] = stoch_rsi_df.iloc[:, 0] # First column is K
            df['STOCHRSI_D'] = stoch_rsi_df.iloc[:, 1] # Second column is D
        else:
            df['STOCHRSI_K'] = pd.NA
            df['STOCHRSI_D'] = pd.NA
            print(f"Warning: StochRSI calculation did not return data for {ticker_symbol}")

        # Prepare data for JavaScript
        ema50_js_data = self._format_series_for_js(df['EMA_50'])
        ema200_js_data = self._format_series_for_js(df['EMA_200'])
        stoch_rsi_k_js_data = self._format_series_for_js(df['STOCHRSI_K'])
        stoch_rsi_d_js_data = self._format_series_for_js(df['STOCHRSI_D'])

        print(f"Indicators calculated for {ticker_symbol}. EMA50 points: {len(ema50_js_data)}, StochRSI_K points: {len(stoch_rsi_k_js_data)}")

        output_filename = f"{ticker_symbol.replace(':', '_').replace('/', '_')}_{interval}_chart.png"
        output_filepath = os.path.join(self.output_dir, output_filename)
        
        async with async_playwright() as p:
            browser = None
            page = None
            try:
                print(f"Playwright: Launching browser for {ticker_symbol}...")
                browser = await p.chromium.launch(headless=True) # Keep headless=True for server
                page = await browser.new_page()
                
                if not os.path.exists(self.template_path):
                    print(f"CRITICAL ERROR: Chart HTML template file not found at {self.template_path}")
                    return None # No finally block here as browser might not be initialized
                
                await page.goto(f"file://{self.template_path}")
                print(f"Playwright: Loaded HTML template: file://{self.template_path}")

                await page.wait_for_function("typeof window.renderChart === 'function'", timeout=10000)
                print("Playwright: window.renderChart function is available.")

                # Construct the data payload for JS
                js_render_args = [
                    ohlc_js_list,
                    volume_js_list,
                    stoch_rsi_k_js_data,
                    stoch_rsi_d_js_data,
                    ema50_js_data,
                    ema200_js_data,
                    ticker_symbol,
                    self.chart_width,
                    self.chart_height # This is for the wrapper, JS calculates internal pane heights
                ]
                
                # This will call window.renderChart with arguments unpacked
                await page.evaluate("([ohlcv, vol, stochK, stochD, ema50, ema200, ticker, width, height]) => window.renderChart(ohlcv, vol, stochK, stochD, ema50, ema200, ticker, width, height)", js_render_args)
                print(f"Playwright: Chart rendering initiated for {ticker_symbol} via JS call.")
                
                # The renderChart in HTML now returns a promise that resolves after a short timeout
                # Playwright's evaluate will await this promise.
                # We can add an additional explicit wait if needed, or wait for a custom signal.
                await page.wait_for_timeout(1500) # Extra wait for complex rendering/slower systems
                print(f"Playwright: Waited for rendering for {ticker_symbol}.")

                chart_wrapper_element = await page.query_selector('#chart-container-wrapper')
                if not chart_wrapper_element:
                    print("Playwright ERROR: Chart wrapper #chart-container-wrapper not found after rendering attempt.")
                    return None # No finally as browser might be an issue

                image_bytes = await chart_wrapper_element.screenshot()
                
                if return_bytes:
                    print(f"Playwright: Screenshot captured as bytes for {ticker_symbol}.")
                    return BytesIO(image_bytes)
                else:
                    with open(output_filepath, "wb") as f:
                        f.write(image_bytes)
                    print(f"Playwright: Screenshot saved to {output_filepath}")
                    return output_filepath
            
            except Exception as e:
                print(f"Playwright error for {ticker_symbol}: {e}")
                if page:
                    try:
                        page_content = await page.content()
                        print(f"Page content at time of Playwright error ({ticker_symbol}):\\n{page_content[:1000]}...")
                    except Exception as pe_content:
                        print(f"Could not get page content after Playwright error: {pe_content}")
                return None
            finally:
                if browser and browser.is_connected():
                    await browser.close()
                    print(f"Playwright: Browser closed for {ticker_symbol}.")

# Example Usage (Updated):
async def main():
    print("--- Testing LightweightChartGenerator (with Alpha Vantage & .env config) ---")
    generator = LightweightChartGenerator(
        template_dir="backend/templates", 
        output_dir="generated_reports"
    )

    # Using only one test case to be mindful of potential API limits
    test_cases = [
        {"ticker": "IBM", "days": 30, "interval": "60min"}, 
        # {"ticker": "MSFT", "days": 30, "interval": "1h"},      
        # {"ticker": "BTC-USD", "days": 90, "interval": "4h"},   
        # {"ticker": "ETH-USD", "days": 45, "interval": "30m"},  
    ]

    for case in test_cases:
        ticker, days, interval = case["ticker"], case["days"], case["interval"]
        print(f"\n--- Generating chart for {ticker} (days: {days}, interval: {interval}) --- (Save to file)")
        
        # Delay already present in data_fetcher if multiple calls happen there.
        # No need for an additional sleep here unless specifically testing chart_generator rate limits itself.
        # await asyncio.sleep(5) 
        
        filepath = await generator.generate_chart_image(ticker, days=days, interval=interval, return_bytes=False)
        if filepath:
            print(f"Chart for {ticker} ({interval}) saved to: {filepath}")
        else:
            print(f"FAILED to generate chart for {ticker} ({interval}).")

    # Test return_bytes (optional, can be commented out to save API calls)
    # print("\n--- Generating chart for NVDA (days: 7, interval: 1h) as bytes ---")
    # await asyncio.sleep(15) # Alpha Vantage has 5 calls/min limit, ensure this doesn't overlap soon 
    # image_bytes_io = await generator.generate_chart_image("NVDA", days=7, interval="1h", return_bytes=True)
    # if image_bytes_io:
    #     print(f"Chart for NVDA as BytesIO object: {type(image_bytes_io)}. Size: {image_bytes_io.getbuffer().nbytes} bytes.")
    # else:
    #     print("FAILED to generate chart for NVDA as bytes.")

if __name__ == "__main__":
    asyncio.run(main()) 