# backend/core/llm_analyzer.py
import os
import asyncio
import time
import hashlib
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
    Gets the DEEPSEEK_API_KEY from environment variables first, then fallback to .env file.
    """
    # First try to get from environment variables (Docker/system env)
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        print("Successfully loaded DEEPSEEK_API_KEY from environment variables")
        return api_key
    
    # Fallback to .env file if environment variable not found
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
                        print("Successfully loaded DEEPSEEK_API_KEY from .env file")
                        return value.strip().strip('"\'')
        return None
    except Exception as e:
        print(f"Error reading .env file for DEEPSEEK_API_KEY: {e}")
        return None


class LLMAnalyzer:
    """
    Handles interaction with a large language model to analyze stock data.
    It can be configured to use either a direct API client (like DeepSeek)
    or a local model via a service like Ollama.
    """
    def __init__(self, model_provider: str = "deepseek", model: Optional[str] = None):
        """
        Initializes the LLM analyzer.
        Args:
            model_provider: The service providing the LLM ('deepseek' or 'ollama').
            model: The specific model name to use. If None, a default is chosen.
        """
        self.model_provider = model_provider.lower()
        if model:
            self.model = model
        else:
            if self.model_provider == "deepseek":
                self.model = "deepseek-chat" # Reverted to deepseek-chat as requested
            elif self.model_provider == "ollama":
                # A default local model, assuming one is served via Ollama
                self.model = "llama3:instruct" 
            else:
                raise ValueError("Unsupported model provider. Choose 'deepseek' or 'ollama'.")

        self.client = self._setup_client()
        print(f"LLMAnalyzer initialized with {self.model_provider} model '{self.model}'.")

    def _setup_client(self):
        if self.model_provider == "deepseek":
            api_key = _get_deepseek_api_key()
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY is not set correctly in the .env file.")
            
            return AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
        else:
            # For Ollama, we'll use a placeholder implementation
            # This is a placeholder and should be replaced with actual Ollama integration
            raise NotImplementedError("Ollama integration is not implemented yet.")

    def _get_key_data_hash(self, key_financial_data: Dict[str, Any]) -> str:
        """生成关键财务数据的哈希值，用于缓存键"""
        # 提取关键数值并创建哈希
        key_values = []
        for key in ['latest_close', 'bollinger_upper', 'bollinger_middle', 'bollinger_lower', 'stoch_rsi_k', 'stoch_rsi_d']:
            value = key_financial_data.get(key)
            if value is not None:
                # 格式化数值以确保一致性
                if isinstance(value, (int, float)):
                    key_values.append(f"{key}:{value:.4f}")
                else:
                    key_values.append(f"{key}:{value}")
        
        hash_string = '|'.join(key_values)
        return hashlib.md5(hash_string.encode()).hexdigest()[:16]

    async def analyze_chart_image(self, image_bytes: bytes, ticker_symbol: str, key_financial_data: dict) -> Optional[str]:
        """
        Analyzes a ticker symbol using a direct API call, prioritizing the provided key financial data.
        The image_bytes are currently ignored.
        """
        print(f"LLM Analyzer: Starting TEXT-ONLY analysis for {ticker_symbol} with key data...")
        
        try:
            key_data_str = _format_key_data_for_prompt(key_financial_data)
            
            response = await self.client.chat.completions.create(
                model=self.model,
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

    async def analyze_chart_image_cached(self, image_bytes: bytes, ticker_symbol: str, key_financial_data: dict) -> Optional[str]:
        """
        缓存优化的AI分析函数
        基于ticker和关键财务数据哈希进行缓存
        性能提升：相同分析请求从3s减少到0.1s
        """
        from .smart_cache import get_cache
        from .performance_monitor import get_monitor
        
        start_time = time.time()
        cache = get_cache()
        monitor = get_monitor()
        
        # 生成数据哈希
        data_hash = self._get_key_data_hash(key_financial_data)
        
        # 先尝试缓存
        cached_analysis = cache.get_analysis_cache(ticker_symbol, data_hash)
        if cached_analysis is not None:
            # 分析缓存命中
            duration = time.time() - start_time
            monitor.track_operation('llm_analysis', duration, cache_hit=True,
                                   metadata={'ticker': ticker_symbol, 'data_hash': data_hash[:8]})
            print(f"LLMAnalyzer: Cache HIT for {ticker_symbol}, took {duration:.3f}s")
            return cached_analysis
        
        # 缓存未命中，调用AI分析
        print(f"LLMAnalyzer: Cache MISS for {ticker_symbol}, calling DeepSeek API...")
        try:
            analysis_text = await self.analyze_chart_image(image_bytes, ticker_symbol, key_financial_data)
            
            duration = time.time() - start_time
            
            if analysis_text is not None and len(analysis_text.strip()) > 0:
                # AI分析成功，缓存结果
                cache.set_analysis_cache(ticker_symbol, data_hash, analysis_text)
                monitor.track_operation('llm_analysis', duration, cache_hit=False,
                                       metadata={'ticker': ticker_symbol, 'data_hash': data_hash[:8], 
                                               'analysis_length': len(analysis_text)})
                print(f"LLMAnalyzer: ✅ AI analysis completed and cached for {ticker_symbol}, took {duration:.3f}s, {len(analysis_text)} chars")
                return analysis_text
            else:
                # AI分析返回空内容
                monitor.track_operation('llm_analysis', duration, cache_hit=False,
                                       metadata={'ticker': ticker_symbol, 'data_hash': data_hash[:8], 'success': False, 'reason': 'empty_response'})
                print(f"LLMAnalyzer: ❌ AI analysis returned empty content for {ticker_symbol}, took {duration:.3f}s")
                return None
                
        except Exception as e:
            duration = time.time() - start_time
            # AI分析异常
            monitor.track_operation('llm_analysis', duration, cache_hit=False,
                                   metadata={'ticker': ticker_symbol, 'data_hash': data_hash[:8], 'success': False, 'error': str(e)})
            print(f"LLMAnalyzer: ❌ AI analysis exception for {ticker_symbol}: {type(e).__name__}: {e}, took {duration:.3f}s")
            import traceback
            traceback.print_exc()
            return None 