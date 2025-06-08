# scripts/convert_report_cli.py
import argparse
import json
import os
import sys

# Add the project root to the Python path to allow imports from 'backend'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import our modules
from backend.core.report_converter import ReportConverter

def main():
    """
    Command-line interface for converting a markdown report and a chart image into a single image.
    """
    parser = argparse.ArgumentParser(description="Generate a report image from markdown, a chart, and metadata.")
    parser.add_argument("--markdown-file", required=True, help="Path to the input markdown file.")
    parser.add_argument("--chart-file", required=True, help="Path to the chart image file.")
    parser.add_argument("--output-file", required=True, help="Path to save the final report image.")
    parser.add_argument("--ticker", required=True, help="Stock ticker symbol.")
    parser.add_argument("--interval", required=True, help="Data interval (e.g., '1d').")
    parser.add_argument("--key-data-json", required=True, help="JSON string of key financial data.")
    parser.add_argument("--author", required=False, default="AI Analyst", help="Author of the report.")
    parser.add_argument("--avatar-path", required=False, help="Path to the author's avatar image.")
    
    args = parser.parse_args()

    print("--- Starting Report Conversion CLI Script ---")
    
    if not os.path.exists(args.markdown_file):
        print(f"Error: Markdown file not found at {args.markdown_file}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.chart_file):
        print(f"Error: Chart file not found at {args.chart_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.markdown_file, "r", encoding="utf-8") as f:
            markdown_text = f.read()
    except Exception as e:
        print(f"Error reading markdown file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        key_data = json.loads(args.key_data_json)
    except json.JSONDecodeError as e:
        print(f"Error decoding key_data JSON: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Successfully parsed arguments.")
    print(f"Ticker: {args.ticker}, Interval: {args.interval}")
    print(f"Outputting final report to: {args.output_file}")

    converter = ReportConverter()
    
    success = converter.markdown_to_image(
        markdown_text=markdown_text,
        chart_image_path=args.chart_file,
        output_image_path=args.output_file,
        ticker=args.ticker,
        interval=args.interval,
        key_data=key_data,
        author=args.author,
        avatar_path=args.avatar_path
    )

    if success:
        print(f"--- Report Conversion CLI Script Finished Successfully ---")
        sys.exit(0)
    else:
        print(f"--- Report Conversion CLI Script Failed ---")
        sys.exit(1)

if __name__ == "__main__":
    main() 