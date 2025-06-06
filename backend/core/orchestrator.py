# backend/core/orchestrator.py
import asyncio
import os
from datetime import datetime
from typing import Optional

# The imports are now simplified as we've consolidated logic
from backend.core import data_fetcher
from backend.core.chart_generator import ChartGenerator
from backend.core.llm_analyzer import LLMAnalyzer
from backend.core.report_converter import ReportConverter

class AnalysisOrchestrator:
    def __init__(self, output_dir: str = "generated_reports"):
        # The orchestrator now directly uses the data_fetcher functions
        # and no longer instantiates a DataFetcher class.
        self.chart_generator = ChartGenerator(output_dir=output_dir)
        self.llm_analyzer = LLMAnalyzer()
        self.report_converter = ReportConverter(width=860)
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        print(f"AnalysisOrchestrator initialized. Output directory: {self.output_dir}")

    async def generate_report(
        self,
        ticker_symbol: str,
        days_back: int = 30,
        interval: str = "1h"
    ):
        print(f"--- Orchestrator: Starting report for {ticker_symbol} ---")
        
        # Normalize ticker to uppercase
        ticker_symbol = ticker_symbol.upper()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = os.path.join(self.output_dir, f"report_{ticker_symbol}_{interval}_{timestamp}")
        os.makedirs(report_dir, exist_ok=True)
        print(f"Orchestrator: Created output directory: {report_dir}")

        # 1. Fetch data directly using the function
        js_data, raw_df = await data_fetcher.get_ohlcv_data(
            ticker_symbol=ticker_symbol,
            days_history=days_back,
            interval=interval
        )
        if raw_df is None or raw_df.empty:
            print(f"Orchestrator: Failed to fetch data for {ticker_symbol}. Aborting.")
            return

        # 2. Generate Chart Image from the dataframe
        chart_image_bytes, key_data = await self.chart_generator.generate_chart_from_df(
            raw_df=raw_df,
            ticker_symbol=ticker_symbol,
            interval=interval,
        )
        if not chart_image_bytes:
            print(f"Orchestrator: Failed to generate chart for {ticker_symbol}. Aborting.")
            return
        
        chart_image_path = os.path.join(report_dir, "chart.png")
        with open(chart_image_path, "wb") as f:
            f.write(chart_image_bytes)
        print(f"Orchestrator: Chart image saved to {chart_image_path}")

        # 3. Get AI Analysis (now a direct async call)
        analysis_text = await self.llm_analyzer.analyze_chart_image(
            image_bytes=chart_image_bytes, 
            ticker_symbol=ticker_symbol,
            key_financial_data=key_data
        )
        if not analysis_text:
            print(f"Orchestrator: Failed to get analysis from LLM for {ticker_symbol}. Aborting.")
            return

        # 4. Save Markdown and Combine into a final report image
        full_markdown_content = analysis_text
        
        markdown_path = os.path.join(report_dir, "analysis.md")
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(full_markdown_content)
        print(f"Orchestrator: Markdown analysis saved to {markdown_path}")

        report_image_path = os.path.join(report_dir, "final_report.png")
        success = await self.report_converter.markdown_to_image(
            markdown_text=full_markdown_content,
            chart_image_path=chart_image_path,
            output_image_path=report_image_path
        )

        if success:
            print(f"--- Orchestrator: Final report image for {ticker_symbol} successfully generated at {report_image_path} ---")
        else:
            print(f"--- Orchestrator: Failed to generate final report image for {ticker_symbol}. ---")


async def main_test():
    """Function to test the orchestrator."""
    print("--- Testing Analysis Orchestrator ---")
    orchestrator = AnalysisOrchestrator()
    
    # --- Test Case 1: Equity (TSLA) ---
    print("\n--- Running Equity Test (TSLA) ---")
    await orchestrator.generate_report("TSLA", days_back=30, interval="1h")

if __name__ == "__main__":
    import sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    asyncio.run(main_test()) 