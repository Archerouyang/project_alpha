# backend/core/chart_generator.py
import os
import pandas as pd
import pandas_ta as ta
import sys
from datetime import datetime, date
from typing import Optional, Tuple, List, Dict, Any

from playwright.sync_api import sync_playwright # Use sync API

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

    def _extract_key_data(self, df_with_indicators: pd.DataFrame) -> dict:
        """Extracts key financial data points from the final dataframe."""
        latest_row = df_with_indicators.iloc[-1]
        
        key_data = {
            "latest_close": latest_row.get('close'),
            "period_high": df_with_indicators['high'].max(),
            "period_low": df_with_indicators['low'].min(),
            "bollinger_upper": latest_row.get('bbu'),
            "bollinger_middle": latest_row.get('bbm'),
            "bollinger_lower": latest_row.get('bbl'),
            "stoch_rsi_k": latest_row.get('stochk_14_3_3'),
            "stoch_rsi_d": latest_row.get('stochd_14_3_3'),
        }
        
        # 标准化 key_data：布林带保留两位小数，RSI 取整数，其他保留四位小数
        for key, value in key_data.items():
            if value is None or not isinstance(value, (int, float)):
                continue
            if key in ('bollinger_upper', 'bollinger_middle', 'bollinger_lower'):
                key_data[key] = round(value, 2)
            elif key in ('stoch_rsi_k', 'stoch_rsi_d'):
                key_data[key] = int(round(value))
            else:
                key_data[key] = round(value, 4)

        print(f"Extracted Key Data: {key_data}")
        return key_data

    def extract_key_data(self, raw_df: pd.DataFrame) -> Optional[dict]:
        """
        Public method to calculate indicators and extract key data from a raw DataFrame.
        This is a pure data processing method, no browser involved.
        """
        if raw_df is None or raw_df.empty:
            return None
        df_with_indicators = self._calculate_indicators(raw_df)
        return self._extract_key_data(df_with_indicators)

    def generate_chart_from_df(self, raw_df: pd.DataFrame, ticker_symbol: str, interval: str) -> Tuple[Optional[bytes], Optional[dict]]:
        """
        Generates a chart image from a DataFrame using a self-contained, synchronous Playwright instance.
        """
        df_with_indicators = self._calculate_indicators(raw_df)
        ohlc_data, volume_data, stoch_k_data, stoch_d_data = self._format_data_for_js(df_with_indicators)
        indicator_data = self._get_indicator_data_for_js(df_with_indicators)
        key_data_dict = self._extract_key_data(df_with_indicators)
        
        print(f"Playwright: Launching self-contained browser for {ticker_symbol}...")
        try:
            with sync_playwright() as p:
                browser = p.firefox.launch() # Use Firefox
                page = browser.new_page()
                page.on("console", lambda msg: print(f"Browser Console ({msg.type}): {msg.text}"))
                
                template_url = f"file://{self.template_path}"
                page.goto(template_url)
                page.wait_for_function("typeof window.renderChart === 'function'")

                page.evaluate(
                    "(args) => window.renderChart(args)",
                    {
                        "ohlcData": ohlc_data, "volumeData": volume_data, "stochKData": stoch_k_data,
                        "stochDData": stoch_d_data, "bbuData": indicator_data.get('bbu', []),
                        "bbmData": indicator_data.get('bbm', []), "bblData": indicator_data.get('bbl', []),
                        "tickerSymbol": ticker_symbol.upper(), "interval": interval,
                        "chartWidth": 1280, "chartHeight": 720
                    }
                )
                
                page.wait_for_timeout(2000)
                chart_element = page.query_selector('#chart-container-wrapper')
                if not chart_element:
                    raise RuntimeError("Could not find '#chart-container-wrapper' element in HTML.")
                
                image_bytes = chart_element.screenshot()
                browser.close()
                
                print(f"Playwright: Screenshot captured and browser closed for {ticker_symbol}.")
                return image_bytes, key_data_dict
                
        except Exception as e:
            print(f"An error occurred during chart generation for {ticker_symbol}: {e}", file=sys.stderr)
            raise

if __name__ == '__main__':
    # This remains for potential direct testing in the future but is not used by the app.
    print("This script is intended to be used as a module.")