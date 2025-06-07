# backend/core/orchestrator.py
import asyncio
import os
import json
import subprocess
import sys
from datetime import datetime
from typing import Optional, Tuple

# The imports are now simplified as we've consolidated logic
# No longer need to import ChartGenerator or Browser from playwright
from backend.core.llm_analyzer import LLMAnalyzer
from backend.core.report_converter import ReportConverter
from .data_fetcher import get_ohlcv_data

class AnalysisOrchestrator:
    def __init__(self, output_dir: str = "generated_reports"):
        self.output_dir = output_dir
        self.llm_analyzer = LLMAnalyzer()
        # The converter is now only used for its path logic, not its async methods.
        # self.report_converter = ReportConverter()
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"AnalysisOrchestrator initialized. Output directory: {self.output_dir}")

    def _create_report_paths(self, ticker: str, interval: str) -> Tuple[str, str, str, str, str]:
        """Creates and returns paths for the report directory and its contents."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir_name = f"report_{ticker}_{interval}_{timestamp}"
        report_dir = os.path.join(self.output_dir, report_dir_name)
        os.makedirs(report_dir, exist_ok=True)
        print(f"Orchestrator: Created output directory: {report_dir}")

        chart_path = os.path.join(report_dir, "chart.png")
        key_data_path = os.path.join(report_dir, "key_data.json")
        analysis_path = os.path.join(report_dir, "analysis.md")
        final_report_path = os.path.join(report_dir, "final_report.png")
        
        return report_dir, chart_path, key_data_path, analysis_path, final_report_path

    def _run_cli_command(self, command: list, env: Optional[dict] = None) -> bool:
        """
        Runs a command-line interface script as a subprocess, ensuring critical
        environment variables are passed down.
        """
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        # Ensure UTF-8 encoding for all subprocess I/O
        process_env['PYTHONIOENCODING'] = 'utf-8'

        # Explicitly pass API keys to the subprocess environment. This is the most
        # reliable way to ensure the subprocess has the necessary credentials.
        for key in ["FMP_API_KEY", "DEEPSEEK_API_KEY"]:
            value = os.getenv(key)
            if value:
                process_env[key] = value
            else:
                print(f"Orchestrator Warning: {key} not found in the main process environment. The CLI script might fail if it needs it.")

        print(f"Orchestrator: Executing command: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8', # Specify encoding for capturing output
                errors='replace', # Handle potential encoding errors gracefully
                env=process_env
            )
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

    async def generate_report(self, ticker: str, interval: str, num_candles: int) -> Tuple[Optional[str], Optional[str]]:
        print(f"--- Orchestrator: Starting report for {ticker} ---")
        report_dir, chart_path, key_data_path, analysis_path, final_report_path = self._create_report_paths(ticker, interval)
        
        # --- Step 1: Generate Chart and Key Data via CLI ---
        python_executable = sys.executable
        chart_cli_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'generate_chart_cli.py'))
        
        chart_command = [
            python_executable, chart_cli_script,
            "--ticker", ticker, "--interval", interval, "--num-candles", str(num_candles),
            "--output-image", chart_path, "--output-data", key_data_path
        ]

        if not self._run_cli_command(chart_command):
            print(f"Orchestrator: Chart generation failed for {ticker}. Aborting.")
            return None, "Chart generation via CLI script failed."
        
        # --- Step 2: Load generated data and pass to LLM ---
        try:
            with open(chart_path, "rb") as f:
                chart_image_bytes = f.read()
            with open(key_data_path, "r", encoding="utf-8") as f:
                key_data = json.load(f)
            print(f"Orchestrator: Loaded chart and data for {ticker}.")
        except Exception as e:
            print(f"Orchestrator: Failed to load generated chart/data files for {ticker}. Aborting. Error: {e}")
            return None, "Could not load data files generated by the chart script."

        analysis_text = await self.llm_analyzer.analyze_chart_image(chart_image_bytes, ticker, key_data)
        if not analysis_text:
            print(f"Orchestrator: Failed to get analysis from LLM for {ticker}. Aborting.")
            return None, "LLM analysis failed."
        
        with open(analysis_path, "w", encoding="utf-8") as f:
            f.write(analysis_text)
        print(f"Orchestrator: Markdown analysis saved to {analysis_path}")
        
        # --- Step 3: Convert Markdown to Final Report Image via CLI ---
        report_cli_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'convert_report_cli.py'))
        report_command = [
            python_executable, report_cli_script,
            "--markdown-file", analysis_path,
            "--chart-file", chart_path,
            "--output-file", final_report_path
        ]

        if not self._run_cli_command(report_command):
            print(f"--- Orchestrator: Failed to generate final report image for {ticker}. ---")
            return None, "Report conversion via CLI script failed."
        
        # --- Step 4: Final Verification and Return ---
        if not os.path.exists(final_report_path):
            print(f"--- Orchestrator: Final report image not found at expected path for {ticker}. ---")
            return None, "Final report image not found after script execution."
        
        print(f"--- Orchestrator: Successfully generated report for {ticker} at {final_report_path} ---")
        return final_report_path, None

# This part is for direct script execution testing, which is less relevant now.
async def main_test():
    import load_dotenv
    load_dotenv.load_dotenv()
    
    orchestrator = AnalysisOrchestrator()
    # Test with a common stock
    final_report_path, error = await orchestrator.generate_report("AAPL", "1d", 90)
    
    if error:
        print(f"An error occurred: {error}")
    else:
        print(f"Successfully generated report: {final_report_path}")

if __name__ == '__main__':
    # Add sys to path to find python executable for subprocess
    import sys
    asyncio.run(main_test()) 