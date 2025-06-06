# AI Technical Analysis Service

This project is a sophisticated financial analysis service that automatically generates technical analysis reports for stock tickers. It fetches the latest market data, creates detailed candlestick charts with technical indicators, generates an in-depth analysis using a Large Language Model (LLM), and combines them into a single, clean image-based report.

## Features

- **Automated Data Fetching**: Utilizes the OpenBB SDK to fetch historical OHLCV (Open, High, Low, Close, Volume) data for any given stock ticker.
- **Advanced Chart Generation**: Renders high-quality financial charts using the TradingView Lightweight Charts library via Playwright for headless browser automation.
- **Indicator Support**: Automatically calculates and overlays key technical indicators, including Bollinger Bands and Stochastic RSI.
- **AI-Powered Analysis**: Leverages the DeepSeek API to generate a four-paragraph narrative analysis based on a sophisticated prompt grounded in established financial theories (Al Brooks Price Action, etc.).
- **Report Composition**: Combines the generated chart and the AI analysis into a single, shareable image report.
- **Modular Architecture**: Built with a clean, modular structure separating concerns for data fetching, chart generation, AI analysis, and orchestration.

## Technology Stack

- **Backend**: Python 3.11
- **API/Framework**: FastAPI (scaffolding, not fully implemented)
- **Data Source**: OpenBB SDK
- **Chart Rendering**: Playwright & TradingView Lightweight Charts
- **AI Analysis**: DeepSeek API (via the `openai` Python library)
- **Image Manipulation**: Pillow (PIL) was used and later removed; final composition is handled via HTML/CSS rendering in Playwright.
- **Dependency Management**: `uv`

---

## Setup and Installation

1.  **Clone the Repository**:
    ```bash
    git clone <your-repository-url>
    cd project_alpha
    ```

2.  **Create and Activate Virtual Environment**:
    This project uses `uv` for fast dependency management.
    ```bash
    # Install uv if you haven't already
    pip install uv

    # Create and activate the virtual environment
    uv venv
    source .venv/bin/activate  # On Windows, use: .\.venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Set Up API Keys**:
    - Create a file named `.env` in the root of the project directory.
    - Add your DeepSeek and OpenBB API keys to the `.env` file like this:
      ```env
      DEEPSEEK_API_KEY="your_deepseek_api_key"
      OPENBB_API_KEY="your_openbb_api_key" 
      ```
    - The OpenBB key is loaded automatically by their SDK; the DeepSeek key is loaded by our application.

---

## How to Run

The main entry point for generating a report is the `orchestrator.py` script.

-   **Run from the project root directory**:
    ```bash
    python -m backend.core.orchestrator
    ```
-   This will run the default test case for "TSLA" with a "1h" interval. The final report image will be saved in a timestamped folder inside the `generated_reports` directory.

## To-Do / Future Enhancements

- [ ] Implement a full FastAPI backend to expose report generation via an API endpoint.
- [ ] Develop a user-facing frontend to input tickers and view reports.
- [ ] Expand the range of supported technical indicators.
- [ ] Implement multi-modal analysis by sending the chart image to a vision-capable LLM.
- [ ] Add more robust error handling and logging.
- [ ] Containerize the application with Docker for easier deployment. 