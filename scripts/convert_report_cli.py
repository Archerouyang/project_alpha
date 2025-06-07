# scripts/convert_report_cli.py
import argparse
import os
import sys
import json

# Add the project root to the Python path to allow importing from 'backend'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import our modules
from backend.core.report_converter import ReportConverter

def main():
    """
    Command-line interface to convert a markdown file and a chart image
    into a single final report image.
    """
    parser = argparse.ArgumentParser(description="Convert analysis into a polished report image.")
    parser.add_argument("--markdown-file", required=True, help="Path to the input markdown file.")
    parser.add_argument("--chart-file", required=True, help="Path to the chart image.")
    parser.add_argument("--output-file", required=True, help="Path to save the final report image.")
    parser.add_argument("--ticker", required=True, help="Ticker symbol for the report header.")
    parser.add_argument("--interval", required=True, help="Interval for the report header.")
    parser.add_argument("--key-data-json", required=True, help="JSON string of key data for the dashboard.")
    parser.add_argument("--author", help="Author signature for the footer.")
    parser.add_argument("--avatar-path", help="Path to the author's avatar image.")
    parser.add_argument("--width", type=int, default=800, help="Width of the report image.")
    args = parser.parse_args()

    print("CLI (Report): Starting report conversion...")

    # 1. Read markdown content
    try:
        with open(args.markdown_file, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        print(f"CLI (Report): Successfully read markdown file: {args.markdown_file}")
    except FileNotFoundError:
        print(f"CLI (Report): Error - Markdown file not found at {args.markdown_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"CLI (Report): Error reading markdown file: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Parse key data
    try:
        key_data = json.loads(args.key_data_json)
    except json.JSONDecodeError as e:
        print(f"CLI Error: Failed to parse key_data_json: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Convert to image
    try:
        converter = ReportConverter(width=args.width)
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
        if not success:
            raise RuntimeError("The conversion method returned False.")
        print(f"CLI (Report): Conversion process completed successfully.")
    except Exception as e:
        print(f"CLI (Report): An error occurred during report conversion: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 