import os
import json
import re
from openai import AsyncOpenAI
from typing import Dict, Any, Optional

# Simple in-memory cache for common instructions
_instruction_cache: Dict[str, Dict[str, Any]] = {}

# It's good practice to get the API key from environment variables
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY environment variable not set.")

# Initialize the AsyncOpenAI client
# It's better to initialize it once and reuse it.
client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

# Simplified system prompt for faster processing
SYSTEM_PROMPT = """
You are a stock analysis command validator. Respond ONLY with JSON.

Valid format: `[TICKER] [EXCHANGE?] [INTERVAL?] [NUM_CANDLES?]`
- TICKER: Required (e.g., AAPL, BTC-USD)
- EXCHANGE: Optional for crypto (e.g., KRAKEN) 
- INTERVAL: Optional (e.g., 1h, 1d), default 1d
- NUM_CANDLES: Optional number, default 150

Response format:
- status: "valid" | "clarification_needed" | "irrelevant"
- command: corrected command string or null
- explanation: cute response with emojis as AI girl assistant

Examples:
Input: "苹果公司" → {"status": "valid", "command": "AAPL 1d 150", "explanation": "收到主人！帮您分析苹果(AAPL)～ ✨"}
Input: "写诗" → {"status": "irrelevant", "command": null, "explanation": "呜...我只会看K线图啦 (´；ω；｀)"}
"""

def _normalize_input(user_input: str) -> str:
    """Normalize user input for caching"""
    return user_input.strip().lower()

def _parse_simple_command(user_input: str) -> Optional[Dict[str, Any]]:
    """
    Fast local parsing for common command formats
    Returns parsed result if successful, None if needs LLM processing
    """
    # Remove extra whitespace and normalize
    text = user_input.strip().upper()
    
    # Pattern 1: Simple ticker (AAPL, TSLA, etc.)
    if re.match(r'^[A-Z]{1,5}(-[A-Z]{3})?$', text):
        return {
            "status": "valid",
            "command": f"{text} 1d 150",
            "explanation": f"收到主人！马上分析 {text} 的走势～ ✨"
        }
    
    # Pattern 2: Ticker + interval (AAPL 1h, TSLA 4h, etc.)
    match = re.match(r'^([A-Z]{1,5}(?:-[A-Z]{3})?)\s+(\d+[HMWD])$', text)
    if match:
        ticker, interval = match.groups()
        return {
            "status": "valid", 
            "command": f"{ticker} {interval.lower()} 150",
            "explanation": f"了解！{ticker} {interval} 图表分析马上来～ 🚀"
        }
    
    # Pattern 3: Ticker + exchange + interval (BTC-USD KRAKEN 1h)
    match = re.match(r'^([A-Z-]{3,10})\s+([A-Z]{4,10})\s+(\d+[HMWD])$', text)
    if match:
        ticker, exchange, interval = match.groups()
        return {
            "status": "valid",
            "command": f"{ticker} {exchange} {interval.lower()} 150", 
            "explanation": f"收到！{exchange}交易所的{ticker} {interval}图分析～ ⚡"
        }
    
    # If no pattern matches, needs LLM processing
    return None

async def validate_and_extract_command(user_input: str) -> Dict[str, Any]:
    """
    Uses fast local parsing first, then LLM for complex cases.
    Includes caching for improved performance.
    """
    # Check cache first
    cache_key = _normalize_input(user_input)
    if cache_key in _instruction_cache:
        return _instruction_cache[cache_key]
    
    # Try fast local parsing first
    local_result = _parse_simple_command(user_input)
    if local_result:
        # Cache the result
        _instruction_cache[cache_key] = local_result
        return local_result
    
    # Fallback to LLM for complex/ambiguous inputs
    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            max_tokens=150,  # Reduced from 200
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty response")
        parsed_content = json.loads(content)

        # Basic validation
        if not all(k in parsed_content for k in ["status", "command", "explanation"]):
            raise ValueError("LLM response is missing required keys.")

        # Cache the result
        _instruction_cache[cache_key] = parsed_content
        return parsed_content

    except json.JSONDecodeError:
        print(f"Error: LLM did not return valid JSON. Response: {content}")
        fallback = {
            "status": "clarification_needed",
            "command": None,
            "explanation": "处理您的请求时遇到一点小问题，您能换个方式再问一次吗？"
        }
        _instruction_cache[cache_key] = fallback
        return fallback
        
    except Exception as e:
        print(f"An unexpected error occurred in instruction validator: {e}")
        fallback = {
            "status": "clarification_needed", 
            "command": None,
            "explanation": "抱歉，我的大脑好像短路了... 能请您再说一遍您的指令吗？"
        }
        _instruction_cache[cache_key] = fallback
        return fallback

def clear_instruction_cache():
    """Clear the instruction cache (for testing/debugging)"""
    global _instruction_cache
    _instruction_cache.clear()

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return {
        "cached_instructions": len(_instruction_cache),
        "cache_keys": list(_instruction_cache.keys())[:10]  # Show first 10 for debugging
    } 