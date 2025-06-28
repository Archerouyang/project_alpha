# backend/core/orchestrator.py
import asyncio
import os
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime
from typing import Optional, Tuple

import pandas as pd
from backend.core.chart_generator import ChartGenerator
from backend.core.llm_analyzer import LLMAnalyzer
from .data_fetcher import get_ohlcv_data_cached
from backend.db.reports import init_db, insert_report
from zoneinfo import ZoneInfo

class AnalysisOrchestrator:
    def __init__(self, output_dir: str = "generated_reports"):
        # 初始化报告数据库
        init_db()
        self.output_dir = output_dir
        self.llm_analyzer = LLMAnalyzer()
        self.chart_generator = ChartGenerator()
        
        # 初始化缓存和性能监控
        from .smart_cache import get_cache
        from .performance_monitor import get_monitor
        self.cache = get_cache()
        self.monitor = get_monitor()
        
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"AnalysisOrchestrator initialized with smart cache. Output directory: {self.output_dir}")

    def _create_report_paths(self, ticker: str, interval: str) -> Tuple[str, str, str, str, str]:
        """Creates and returns paths for the report directory and its contents."""
        # 按日期分目录存储
        date_str = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
        date_dir = os.path.join(self.output_dir, date_str)
        os.makedirs(date_dir, exist_ok=True)
        # 使用北京时间戳作为目录名一部分
        timestamp = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d_%H%M%S")
        report_dir_name = f"report_{ticker}_{interval}_{timestamp}"
        report_dir = os.path.join(date_dir, report_dir_name)
        os.makedirs(report_dir, exist_ok=True)
        print(f"Orchestrator: Created output directory: {report_dir}")

        temp_data_filename = f"data_{uuid.uuid4()}.json"
        temp_data_path = os.path.join(report_dir, temp_data_filename)

        chart_path = os.path.join(report_dir, "chart.png")
        analysis_path = os.path.join(report_dir, "analysis.md")
        final_report_path = os.path.join(report_dir, "final_report.png")
        
        return report_dir, temp_data_path, chart_path, analysis_path, final_report_path

    async def _run_cli_in_executor(self, command: list) -> bool:
        """Runs a blocking CLI command in a separate thread to avoid blocking the asyncio event loop."""
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._run_cli_command, command)
        return result

    def _run_cli_command(self, command: list, env: Optional[dict] = None) -> bool:
        """
        Runs a command-line interface script as a subprocess.
        """
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        process_env['PYTHONIOENCODING'] = 'utf-8'

        for key in ["FMP_API_KEY", "DEEPSEEK_API_KEY"]:
            value = os.getenv(key)
            if value:
                process_env[key] = value

        print(f"Orchestrator: Executing command: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=process_env
            )
            if result.stdout:
                print("Orchestrator: CLI script stdout:")
                print(result.stdout)
            if result.stderr:
                print("Orchestrator: CLI script stderr:")
                print(result.stderr)
            return True
        except subprocess.CalledProcessError as e:
            print("Orchestrator: CLI script failed with an error.")
            print(f"Return Code: {e.returncode}")
            print(f"Stdout:\n{e.stdout}")
            print(f"Stderr:\n{e.stderr}")
            return False
        except Exception as e:
            print(f"Orchestrator: An unexpected error occurred while running the CLI script: {e}")
            return False

    async def generate_report(self, ticker: str, interval: str, num_candles: int, exchange: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        total_start_time = time.monotonic()
        print(f"🚀 === Orchestrator: Starting CACHED report for {ticker} (Exchange: {exchange or 'N/A'}) ===")
        
        report_dir, temp_data_path, chart_path, analysis_path, final_report_path = self._create_report_paths(ticker, interval)
        
        # === Phase 1: 缓存优化的数据获取 ===
        print(f"\n📊 Phase 1: Smart Data Fetching for {ticker}...")
        time_s1_fetch_start = time.monotonic()
        
        # 使用缓存版本的数据获取
        loop = asyncio.get_running_loop()
        _, ohlcv_df = await loop.run_in_executor(
            None, get_ohlcv_data_cached, ticker, interval, num_candles, exchange
        )

        if ohlcv_df is None or ohlcv_df.empty:
            print(f"❌ Orchestrator: Failed to fetch data for {ticker}. Aborting.")
            self.monitor.track_request(False, time.monotonic() - total_start_time)
            return None, "Data fetching failed."
        
        # Save data to temp file for the CLI script, using a robust orientation
        ohlcv_df.to_json(temp_data_path, orient='split')
        time_s1_fetch_end = time.monotonic()
        
        fetch_duration = time_s1_fetch_end - time_s1_fetch_start
        print(f"✅ Phase 1 completed in {fetch_duration:.2f}s - Data shape: {ohlcv_df.shape}")

        # === Phase 2: 关键数据提取 ===
        print(f"\n🔢 Phase 2: Key Data Extraction...")
        key_data = self.chart_generator.extract_key_data(ohlcv_df)
        if not key_data:
            print(f"❌ Orchestrator: Failed to calculate key data for {ticker}. Aborting.")
            self.monitor.track_request(False, time.monotonic() - total_start_time)
            return None, "Key data calculation failed."
        
        print(f"✅ Phase 2 completed - Key data extracted: {len(key_data)} indicators")

        # === Phase 3: 并行缓存优化执行 ===
        print(f"\n⚡ Phase 3: Parallel Cached Execution (Chart + AI Analysis)")
        time_s3_parallel_start = time.monotonic()

        # 并行执行图表生成和AI分析（都使用缓存版本）
        chart_task = asyncio.create_task(self._generate_chart_cached(ohlcv_df, ticker, interval, chart_path))
        llm_task = asyncio.create_task(self.llm_analyzer.analyze_chart_image_cached(b'', ticker, key_data))

        results = await asyncio.gather(chart_task, llm_task, return_exceptions=True)
        time_s3_parallel_end = time.monotonic()

        parallel_duration = time_s3_parallel_end - time_s3_parallel_start
        print(f"✅ Phase 3 completed in {parallel_duration:.2f}s")

        chart_success, analysis_text = None, None
        for result in results:
            if isinstance(result, bool):
                chart_success = result
            elif isinstance(result, str):
                analysis_text = result
            elif isinstance(result, Exception):
                print(f"❌ Orchestrator: Error in parallel execution: {result}")
                self.monitor.track_request(False, time.monotonic() - total_start_time)
                return None, f"Parallel task error: {result}"
        
        if not chart_success or not os.path.exists(chart_path):
            print(f"❌ Orchestrator: Chart generation failed for {ticker}.")
            self.monitor.track_request(False, time.monotonic() - total_start_time)
            return None, "Chart generation failed."

        if not analysis_text:
            print(f"❌ Orchestrator: LLM analysis failed for {ticker}.")
            self.monitor.track_request(False, time.monotonic() - total_start_time)
            return None, "LLM analysis failed."

        # === Phase 4: 报告合成 ===
        print(f"\n📄 Phase 4: Report Synthesis...")
        with open(analysis_path, "w", encoding="utf-8") as f:
            f.write(analysis_text)
        print(f"✅ Analysis saved to {analysis_path}")
        
        time_s4_convert_start = time.monotonic()
        report_cli_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'convert_report_cli.py'))
        
        key_data_json_string = json.dumps(key_data)

        report_command = [
            sys.executable, report_cli_script,
            "--markdown-file", analysis_path,
            "--chart-file", chart_path,
            "--output-file", final_report_path,
            "--ticker", ticker,
            "--interval", interval,
            "--key-data-json", key_data_json_string,
            "--author", "Archerouyang",
            "--avatar-path", "assets/mc.png"
        ]
        if not await self._run_cli_in_executor(report_command):
            print(f"❌ Orchestrator: Failed to generate final report for {ticker}.")
            self.monitor.track_request(False, time.monotonic() - total_start_time)
            return None, "Report conversion failed."
        
        time_s4_convert_end = time.monotonic()
        synthesis_duration = time_s4_convert_end - time_s4_convert_start
        print(f"✅ Phase 4 completed in {synthesis_duration:.2f}s")
        
        if not os.path.exists(final_report_path):
            print(f"❌ Orchestrator: Final report not found at {final_report_path}.")
            self.monitor.track_request(False, time.monotonic() - total_start_time)
            return None, "Final report not found."
        
        # === 清理和统计 ===
        try:
            os.remove(temp_data_path)
            print(f"🧹 Cleaned up temporary file: {temp_data_path}")
        except OSError as e:
            print(f"⚠️ Error cleaning up temporary file: {e}")

        # 插入报告索引
        generated_at = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
        insert_report(
            None,
            ticker,
            interval,
            final_report_path,
            generated_at,
            key_data.get("latest_close"),
            key_data.get("bollinger_upper"),
            key_data.get("bollinger_middle"),
            key_data.get("bollinger_lower"),
            key_data.get("stoch_rsi_k"),
            key_data.get("stoch_rsi_d")
        )

        # === 性能统计 ===
        total_duration = time.monotonic() - total_start_time
        
        # 记录完整请求统计
        self.monitor.track_request(True, total_duration)
        self.monitor.track_operation('report_generation', total_duration, cache_hit=False,
                                    metadata={'ticker': ticker, 'interval': interval, 'total_phases': 4})
        
        print(f"\n🎉 === CACHE-OPTIMIZED REPORT COMPLETED ===")
        print(f"📊 Performance Summary:")
        print(f"   📈 Data Fetch: {fetch_duration:.2f}s")
        print(f"   ⚡ Parallel Exec: {parallel_duration:.2f}s") 
        print(f"   📄 Report Synthesis: {synthesis_duration:.2f}s")
        print(f"   ⏱️ Total Time: {total_duration:.2f}s")
        print(f"   📁 Report saved: {final_report_path}")
        
        # 显示缓存统计
        cache_stats = self.cache.get_cache_stats()
        hit_rates = self.monitor.get_cache_hit_rates()
        print(f"\n💾 Cache Performance:")
        for cache_type, rate in hit_rates.items():
            print(f"   {cache_type.capitalize()}: {rate:.1f}% hit rate")
        
        return final_report_path, "Report generated successfully with smart caching!"

    async def _generate_chart_cached(self, ohlcv_df: pd.DataFrame, ticker: str, interval: str, chart_path: str) -> bool:
        """使用缓存版本生成图表的辅助方法"""
        try:
            # 在线程池中执行同步的Playwright调用
            import asyncio
            loop = asyncio.get_event_loop()
            chart_bytes, _ = await loop.run_in_executor(
                None, 
                self.chart_generator.generate_chart_from_df_cached, 
                ohlcv_df, ticker, interval
            )
            if chart_bytes:
                with open(chart_path, 'wb') as f:
                    f.write(chart_bytes)
                return True
            return False
        except Exception as e:
            print(f"Error in cached chart generation: {e}")
            return False

async def main_test():
    # To run this test, you need a .env file in the project root
    # with DEEPSEEK_API_KEY and FMP_API_KEY
    print("Starting smart cached orchestrator test...")
    
    orchestrator = AnalysisOrchestrator()
    
    # Test with a popular stock
    ticker = "AAPL"
    interval = "1d"
    num_candles = 100
    exchange = None
    
    print(f"Testing cached analysis for {ticker}...")
    
    # Run the first request (should use API calls)
    print("\n=== FIRST REQUEST (Expected: Cache MISS) ===")
    start_time = time.time()
    result_path, message = await orchestrator.generate_report(ticker, interval, num_candles, exchange)
    first_duration = time.time() - start_time
    
    if result_path:
        print(f"✅ First request completed in {first_duration:.2f}s")
        print(f"Report saved to: {result_path}")
    else:
        print(f"❌ First request failed: {message}")
        return
    
    # Wait a moment, then run the second request (should hit cache)
    print("\n=== SECOND REQUEST (Expected: Cache HIT) ===")
    await asyncio.sleep(2)
    start_time = time.time()
    result_path2, message2 = await orchestrator.generate_report(ticker, interval, num_candles, exchange)
    second_duration = time.time() - start_time
    
    if result_path2:
        print(f"✅ Second request completed in {second_duration:.2f}s")
        print(f"Report saved to: {result_path2}")
    else:
        print(f"❌ Second request failed: {message2}")
        return
    
    # Performance comparison
    print(f"\n📊 PERFORMANCE COMPARISON:")
    print(f"   First request (cache miss): {first_duration:.2f}s")
    print(f"   Second request (cache hit): {second_duration:.2f}s")
    if first_duration > 0:
        improvement = ((first_duration - second_duration) / first_duration) * 100
        print(f"   🚀 Performance improvement: {improvement:.1f}%")
    
    # Show detailed performance stats
    monitor = orchestrator.monitor
    performance_report = monitor.generate_report()
    print(f"\n📈 DETAILED PERFORMANCE REPORT:")
    print(performance_report)

if __name__ == "__main__":
    asyncio.run(main_test()) 