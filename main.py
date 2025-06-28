import base64
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from backend.core.orchestrator import AnalysisOrchestrator
from backend.db.reports import get_reports

# Load environment variables from .env file.
# This should be at the top to ensure they are loaded for all modules.
load_dotenv()

# With main.py at the root, we no longer need to manipulate sys.path.
# Python and Uvicorn will handle it correctly.

app = FastAPI()

# --- Pydantic Models ---
class AnalysisRequest(BaseModel):
    ticker: str
    interval: str
    num_candles: int = 150
    exchange: Optional[str] = None

class AnalysisResponse(BaseModel):
    image: str

class InstructionValidationRequest(BaseModel):
    user_input: str

class InstructionValidationResponse(BaseModel):
    status: str  # "valid", "corrected", "clarification_needed"
    command: Optional[str] = None
    explanation: Optional[str] = None

class ReportMetadata(BaseModel):
    id: int
    user_id: Optional[str]
    symbol: str
    interval: str
    filepath: str
    generated_at: str
    latest_close: Optional[float]
    bollinger_upper: Optional[float]
    bollinger_middle: Optional[float]
    bollinger_lower: Optional[float]
    stoch_rsi_k: Optional[float]
    stoch_rsi_d: Optional[float]

class CacheStatsResponse(BaseModel):
    enabled: bool
    memory: Dict[str, Any]
    disk: Dict[str, Any]
    ttl_settings: Dict[str, int]

class CacheOperationResponse(BaseModel):
    success: bool
    message: str
    cleared_count: Optional[int] = None

class PerformanceStatsResponse(BaseModel):
    session: Dict[str, Any]
    cache_hit_rates: Dict[str, float]
    cache_stats: Dict[str, Dict[str, int]]
    operations: Dict[str, Dict[str, Any]]

# --- Static Files & Frontend Serving ---
# Paths are now relative to the project root where main.py is located.
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML file."""
    return FileResponse("frontend/index.html")

# --- API Endpoints ---
@app.post("/api/validate_instruction", response_model=InstructionValidationResponse)
async def validate_instruction(request: InstructionValidationRequest):
    """
    Validates, corrects, or asks for clarification on a user's instruction using an LLM.
    """
    # This is a placeholder. We will implement the actual logic in a new module.
    # For now, let's simulate a "valid" response for testing.
    from backend.core.instruction_validator import validate_and_extract_command
    
    response = await validate_and_extract_command(request.user_input)
    return response

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    print(f"Received analysis request for: {request.ticker} on exchange {request.exchange or 'default'} ({request.interval})")
    try:
        orchestrator = AnalysisOrchestrator()
        
        final_report_path, message = await orchestrator.generate_report(
            ticker=request.ticker,
            interval=request.interval,
            num_candles=request.num_candles,
            exchange=request.exchange
        )
        
        # 检查报告是否成功生成（基于文件路径而不是消息）
        if not final_report_path or not os.path.exists(final_report_path):
            error_msg = message if message and "failed" in message.lower() else "Final report image not found"
            print(f"An error occurred: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Report generation failed: {error_msg}")
        
        # 成功生成报告
        print(f"Report generated successfully: {message}")

        with open(final_report_path, "rb") as image_file:
            image_base64_str = base64.b64encode(image_file.read()).decode("utf-8")

        return AnalysisResponse(image=image_base64_str)
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"An unexpected error occurred in /api/analyze: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")

@app.get("/api/analysis/history", response_model=List[ReportMetadata])
async def get_history(user_id: Optional[str] = None, date: Optional[str] = None):
    """
    列出历史报告。可根据 user_id 和日期(YYYY-MM-DD) 过滤。
    """
    records = get_reports(user_id, date)
    return records

# --- 缓存管理API端点 ---

@app.get("/api/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """
    获取缓存统计信息：命中率、存储大小、条目数量
    """
    try:
        from backend.core.smart_cache import get_cache
        cache = get_cache()
        stats = cache.get_cache_stats()
        return CacheStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@app.post("/api/cache/clear", response_model=CacheOperationResponse)  
async def clear_expired_cache():
    """
    清理过期缓存，返回清理的条目数
    """
    try:
        from backend.core.smart_cache import get_cache
        cache = get_cache()
        cleared_count = cache.clear_expired_cache()
        return CacheOperationResponse(
            success=True,
            message=f"Successfully cleared {cleared_count} expired cache entries",
            cleared_count=cleared_count
        )
    except Exception as e:
        return CacheOperationResponse(
            success=False,
            message=f"Failed to clear expired cache: {str(e)}"
        )

@app.delete("/api/cache/all", response_model=CacheOperationResponse)
async def clear_all_cache():
    """
    清空所有缓存（开发调试用）
    """
    try:
        from backend.core.smart_cache import get_cache
        cache = get_cache()
        cleared_count = cache.clear_all_cache()
        return CacheOperationResponse(
            success=True,
            message=f"Successfully cleared all cache ({cleared_count} entries)",
            cleared_count=cleared_count
        )
    except Exception as e:
        return CacheOperationResponse(
            success=False,
            message=f"Failed to clear all cache: {str(e)}"
        )

# --- 性能监控API端点 ---

@app.get("/api/performance/stats", response_model=PerformanceStatsResponse)
async def get_performance_stats():
    """
    获取详细的性能统计信息
    """
    try:
        from backend.core.performance_monitor import get_monitor
        monitor = get_monitor()
        stats = monitor.get_performance_stats()
        return PerformanceStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")

@app.get("/api/performance/report")
async def get_performance_report():
    """
    生成可读的性能报告
    """
    try:
        from backend.core.performance_monitor import get_monitor
        monitor = get_monitor()
        report = monitor.generate_report()
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate performance report: {str(e)}")

@app.post("/api/performance/reset")
async def reset_performance_stats():
    """
    重置性能统计数据
    """
    try:
        from backend.core.performance_monitor import get_monitor
        monitor = get_monitor()
        monitor.reset_stats()
        return {"success": True, "message": "Performance statistics reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset performance stats: {str(e)}")

# --- 系统健康检查 ---

@app.get("/api/health")
async def health_check():
    """
    系统健康检查，包括缓存和性能监控状态
    """
    try:
        from backend.core.smart_cache import get_cache
        from backend.core.performance_monitor import get_monitor
        
        cache = get_cache()
        monitor = get_monitor()
        
        cache_stats = cache.get_cache_stats()
        hit_rates = monitor.get_cache_hit_rates()
        
        return {
            "status": "healthy",
            "cache": {
                "enabled": cache_stats["enabled"],
                "memory_usage": f"{cache_stats['memory']['usage_percent']:.1f}%",
                "disk_usage": f"{cache_stats['disk']['total_size_mb']:.1f}MB"
            },
            "performance": {
                "cache_hit_rates": hit_rates,
                "monitoring_active": True
            },
            "timestamp": None  # Will be set by FastAPI
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": None
        }

# To run this app (from the project_alpha directory):
# Ensure .venv is activated: source .venv/bin/activate (or .venv\Scripts\activate on Windows)
# Then run: uvicorn backend.main:app --reload 