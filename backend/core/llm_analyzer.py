# backend/core/llm_analyzer.py
import os
import asyncio
from typing import Optional
from openai import AsyncOpenAI

def _get_system_prompt() -> str:
    """Returns the static system prompt for the financial analyst expert."""
    return """You are a professional financial technical analyst, an expert in Al Brooks' Price Action theory, Bollinger Bands, Volume Analysis, and the Stochastic RSI indicator. Your analytical style is decisive and professional, capable of integrating signals from different tools into a coherent analytical narrative and providing clear, actionable trading strategies."""

def _get_user_prompt(ticker_symbol: str) -> str:
    """Returns the user prompt with the specified ticker symbol and instructions."""
    return f"""Based on the stock ticker provided, you must strictly follow the specified analytical tools and report template structure below to generate a technical analysis report. NOTE: You will not be provided with a chart image; your analysis must be based on your general knowledge of the asset's recent price action and technicals.

Mandatory Analytical Tools:
Bollinger Bands: Use standard parameters (e.g., a 20-period Simple Moving Average as the middle band, with the upper and lower bands at +/- 2 standard deviations). Analyze the relationship between the price and the upper, middle, and lower bands; changes in the Bollinger Bandwidth (contraction/Squeeze or expansion); and signals when the price touches or breaks through the bands.
Volume: Analyze changes in volume in conjunction with price movements to determine the health of the trend (e.g., high-volume breakout, low-volume pullback, price-volume divergence).
Stochastic RSI (14): Use to identify overbought/oversold conditions (e.g., with standard parameters like 14,3,3 or 14,14,3,3) and potential momentum shift signals (bullish/bearish crossovers, divergence).
Al Brooks Price Action Theory: Identify key Trend Bars, Signal Bars, Micro Channels, Pullbacks, Breakout Patterns, and major market structures (like Trend Channels or Trading Ranges). Pay special attention to the behavior of candlesticks at key Bollinger Band levels (e.g., middle, upper, and lower bands).
Chart Patterns: Identify key support levels, resistance levels, trendlines, or simple patterns (like double tops/bottoms, flags) based on price action, and use the Bollinger Band boundaries to confirm these structures.

Report Template Structure & Writing Instructions:
IMPORTANT: Your entire response must be written in flowing, holistic paragraphs. Do NOT use bullet points, numbered lists, or any list-like formatting. Each section of the report should be a well-integrated narrative. Your analysis should naturally progress through the following four themes, each in its own paragraph.

First, provide an overall assessment of the trend and market condition. This should include a definitive judgment on the market's direction, a description of recent critical price action, confirmation with volume analysis, and a brief mention of the Stochastic RSI status.

Second, analyze the price action and chart structure in detail. Apply Al Brooks' theory to identify the dominant market structure, pinpoint key support and resistance levels, and provide one or two potential upside or downside price target zones.

Third, offer a comprehensive interpretation of the indicators. Synthesize the signals from Bollinger Bands, volume, and Stochastic RSI into a coherent chain of evidence, elaborating on the specific signals each is providing.

Fourth, conclude with a clear trading strategy and risk management plan. State the core operational bias, provide actionable entry signals, define clear price targets and stop-loss levels, and mention an alternative scenario or conditions for adjusting the position.

Begin Generation
Now, please generate an analysis report for the following target:

Stock Ticker: {ticker_symbol}"""


def _get_deepseek_api_key() -> Optional[str]:
    """
    Reads the DEEPSEEK_API_KEY from the .env file in the project root.
    """
    try:
        dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
        if not os.path.exists(dotenv_path):
            print(f"Warning: .env file not found at {dotenv_path}")
            return None
        
        with open(dotenv_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key.strip() == 'DEEPSEEK_API_KEY':
                        return value.strip().strip('"\'')
        return None
    except Exception as e:
        print(f"Error reading .env file for DEEPSEEK_API_KEY: {e}")
        return None


class LLMAnalyzer:
    def __init__(self):
        self.api_key = _get_deepseek_api_key()
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set correctly in the .env file.")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        print("LLMAnalyzer initialized with DeepSeek model 'deepseek-r1-0528' via direct API.")

    async def analyze_chart_image(self, image_bytes: bytes, ticker_symbol: str) -> Optional[str]:
        """
        Analyzes a ticker symbol using a direct API call to an OpenAI-compatible endpoint.
        The image_bytes are ignored.
        """
        print(f"LLM Analyzer: Starting TEXT-ONLY analysis for {ticker_symbol}...")
        
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": _get_system_prompt()},
                    {"role": "user", "content": _get_user_prompt(ticker_symbol)},
                ],
                max_tokens=2048,
                temperature=0.5,
            )
            analysis_text = response.choices[0].message.content
            print(f"LLM Analyzer: Successfully received text-only analysis for {ticker_symbol}.")
            return analysis_text

        except Exception as e:
            import traceback
            print(f"LLM Analyzer failed for {ticker_symbol}. Full error traceback:")
            traceback.print_exc()
            return None 