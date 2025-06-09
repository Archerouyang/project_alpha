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
from .data_fetcher import get_ohlcv_data
from backend.db.reports import init_db, insert_report
from zoneinfo import ZoneInfo

class AnalysisOrchestrator:
    def __init__(self, output_dir: str = "generated_reports"):
        # 初始化报告数据库
        init_db()
        self.output_dir = output_dir
        self.llm_analyzer = LLMAnalyzer()
        self.chart_generator = ChartGenerator()
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"AnalysisOrchestrator initialized. Output directory: {self.output_dir}")

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
        start_time = time.monotonic()
        print(f"--- Orchestrator: Starting report for {ticker} (Exchange: {exchange or 'N/A'}) ---")
        
        report_dir, temp_data_path, chart_path, analysis_path, final_report_path = self._create_report_paths(ticker, interval)
        
        time_s1_fetch_start = time.monotonic()
        
        # Run the synchronous, blocking data fetcher in a thread to not block the event loop
        loop = asyncio.get_running_loop()
        _, ohlcv_df = await loop.run_in_executor(
            None, get_ohlcv_data, ticker, interval, num_candles, exchange
        )

        if ohlcv_df is None or ohlcv_df.empty:
            print(f"Orchestrator: Failed to fetch data for {ticker}. Aborting.")
            return None, "Data fetching failed."
        # Save data to temp file for the CLI script, using a robust orientation
        ohlcv_df.to_json(temp_data_path, orient='split')
        time_s1_fetch_end = time.monotonic()

        key_data = self.chart_generator.extract_key_data(ohlcv_df)
        if not key_data:
            print(f"Orchestrator: Failed to calculate key data for {ticker}. Aborting.")
            return None, "Key data calculation failed."
        
        print("\n--- Orchestrator: Starting parallel execution of Chart Generation and LLM Analysis ---")
        time_s3_parallel_start = time.monotonic()

        python_executable = sys.executable
        chart_cli_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'generate_chart_cli.py'))
        chart_command = [
            python_executable, chart_cli_script, "--ticker", ticker, "--interval", interval,
            "--input-data-file", temp_data_path, "--output-image", chart_path,
            "--output-data", os.path.join(report_dir, "dummy_key_data.json") 
        ]
        chart_task = self._run_cli_in_executor(chart_command)

        llm_task = self.llm_analyzer.analyze_chart_image(None, ticker, key_data)

        results = await asyncio.gather(chart_task, llm_task, return_exceptions=True)
        time_s3_parallel_end = time.monotonic()

        chart_success, analysis_text = None, None
        for result in results:
            if isinstance(result, bool):
                chart_success = result
            elif isinstance(result, str):
                analysis_text = result
            elif isinstance(result, Exception):
                print(f"Orchestrator: An error occurred during parallel execution: {result}")
                return None, f"An error occurred in a parallel task: {result}"
        
        if not chart_success or not os.path.exists(chart_path):
            print(f"Orchestrator: Chart generation failed for {ticker}. Aborting.")
            return None, "Chart generation via CLI script failed."

        if not analysis_text:
            print(f"Orchestrator: Failed to get analysis from LLM for {ticker}. Aborting.")
            return None, "LLM analysis failed."

        with open(analysis_path, "w", encoding="utf-8") as f:
            f.write(analysis_text)
        print(f"Orchestrator: Markdown analysis saved to {analysis_path}")
        
        time_s4_convert_start = time.monotonic()
        report_cli_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'convert_report_cli.py'))
        
        key_data_json_string = json.dumps(key_data)

        report_command = [
            python_executable, report_cli_script,
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
            print(f"--- Orchestrator: Failed to generate final report image for {ticker}. ---")
            return None, "Report conversion via CLI script failed."
        time_s4_convert_end = time.monotonic()
        
        if not os.path.exists(final_report_path):
            print(f"--- Orchestrator: Final report image not found at expected path for {ticker}. ---")
            return None, "Final report image not found after script execution."
        
        try:
            os.remove(temp_data_path)
            print(f"Orchestrator: Cleaned up temporary file {temp_data_path}")
        except OSError as e:
            print(f"Orchestrator: Error cleaning up temporary file: {e}")

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

        end_time = time.monotonic()

        print("\n--- PERFORMANCE METRICS (Parallel) ---")
        print(f"Data Fetching:         {time_s1_fetch_end - time_s1_fetch_start:.2f}s")
        print(f"Parallel Task Block:   {time_s3_parallel_end - time_s3_parallel_start:.2f}s (Chart Gen + LLM Analysis)")
        print(f"Report Conversion:     {time_s4_convert_end - time_s4_convert_start:.2f}s")
        print("---------------------------")
        print(f"Total Orchestration Time: {end_time - start_time:.2f}s")
        print(f"--- Orchestrator: Successfully generated report for {ticker} at {final_report_path} ---\n")
        
        return final_report_path, None

async def main_test():
    # To run this test, you need a .env file in the project root
    # with DEEPSEEK_API_KEY and FMP_API_KEY
    import load_dotenv
    load_dotenv.load_dotenv()
    
    orchestrator = AnalysisOrchestrator()
    final_report_path, error = await orchestrator.generate_report("NVDA", "1d", 120, None)
    
    if error:
        print(f"An error occurred: {error}")
    else:
        print(f"Successfully generated report: {final_report_path}")

if __name__ == '__main__':
    import sys
    asyncio.run(main_test()) 