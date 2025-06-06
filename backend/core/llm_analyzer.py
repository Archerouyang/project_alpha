# backend/core/llm_analyzer.py
import os
import asyncio
from typing import Optional, Dict, Any
from openai import AsyncOpenAI

def _get_system_prompt() -> str:
    """Returns the static system prompt for the financial analyst expert."""
    return """You are a professional financial technical analyst, an expert in Al Brooks' Price Action theory, Bollinger Bands, Volume Analysis, and the Stochastic RSI indicator. Your analytical style is decisive and professional, capable of integrating signals from different tools into a coherent analytical narrative and providing clear, actionable trading strategies."""

def _format_key_data_for_prompt(key_data: Dict[str, Any]) -> str:
    """Formats the key data dictionary into a string for the LLM prompt."""
    if not key_data:
        return "No key data provided."
    
    lines = [
        "【关键价格与指标参考数据 (请优先使用以下数值进行分析)】",
        f"最新收盘价: {key_data.get('latest_close', 'N/A')}",
        f"图表周期内最高价: {key_data.get('period_high', 'N/A')}",
        f"图表周期内最低价: {key_data.get('period_low', 'N/A')}",
        f"布林带上轨: {key_data.get('bollinger_upper', 'N/A')}",
        f"布林带中轨: {key_data.get('bollinger_middle', 'N/A')}",
        f"布林带下轨: {key_data.get('bollinger_lower', 'N/A')}",
        f"Stochastic RSI %K: {key_data.get('stoch_rsi_k', 'N/A')}",
        f"Stochastic RSI %D: {key_data.get('stoch_rsi_d', 'N/A')}"
    ]
    return "\n".join(lines)

def _get_user_prompt(ticker_symbol: str, key_data_str: str) -> str:
    """Returns the user prompt with the specified ticker symbol and instructions."""
    return f"""{key_data_str}

基于以上提供的【关键价格与指标参考数据】以及您对该股票代码的总体了解，您必须严格遵循指定的分析工具和报告模板结构，生成一份技术分析报告。
注意：您不会收到图表图片，您的分析必须基于您对该资产近期价格行为的总体知识，并严格使用我提供的数值。

**重要指令：** 在提及具体价格水平、支撑、阻力或指标数值时，**请务biyou优先引用和基于我提供的【关键价格与指标参考数据】中的数值**，以确保分析的准确性。

**分析工具（理论框架）:**
Bollinger Bands: 分析价格与布林带三条轨道的关系，带宽的变化，以及价格触及或突破轨道时的信号。
Volume: 结合价格变动分析成交量，以判断趋势的健康状况。
Stochastic RSI (14): 识别超买/超卖状况及潜在的动能转换信号。
Al Brooks Price Action Theory: 识别趋势K线、信号K线、微通道、回调、突破模式及主要市场结构。
Chart Patterns: 识别关键的支撑、阻力、趋势线或简单形态。

**报告模板结构与撰写指令:**
您的整个回应必须是流畅、完整的段落。**禁止使用项目符号、编号列表或任何类似列表的格式。** 报告的每一部分都应是一个整合良好的叙述。您的分析应自然地按以下四个主题展开，每个主题一段。

首先，对趋势和市场状况进行总体评估。
其次，详细分析价格行为和图表结构。
第三，提供对各项指标的综合解读。
最后，以清晰的交易策略和风险管理计划作结。

**开始生成**
现在，请为以下目标生成分析报告:

股票代码: {ticker_symbol}"""


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

    async def analyze_chart_image(self, image_bytes: bytes, ticker_symbol: str, key_financial_data: dict) -> Optional[str]:
        """
        Analyzes a ticker symbol using a direct API call, prioritizing the provided key financial data.
        The image_bytes are currently ignored.
        """
        print(f"LLM Analyzer: Starting TEXT-ONLY analysis for {ticker_symbol} with key data...")
        
        try:
            key_data_str = _format_key_data_for_prompt(key_financial_data)
            
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": _get_system_prompt()},
                    {"role": "user", "content": _get_user_prompt(ticker_symbol, key_data_str)},
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