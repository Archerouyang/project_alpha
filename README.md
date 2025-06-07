# AI-Powered Technical Analysis Service

This project is a sophisticated financial analysis service that automatically generates technical analysis reports for stocks and cryptocurrencies. It fetches the latest market data, creates detailed candlestick charts with technical indicators, generates an in-depth analysis using a Large Language Model (LLM), and combines them into a single, clean image-based report, all accessible through a simple web interface.

## Features

- **Web UI**: A clean, chat-like interface to request and display analysis reports.
- **Equity and Crypto Support**: Intelligently fetches data for both stock tickers (e.g., `AAPL`) and cryptocurrency pairs (e.g., `BTC-USD`).
- **Exchange-Specific Data**: Allows specifying a cryptocurrency exchange (e.g., `KRAKEN`, `BINANCE`) for precise data sourcing.
- **Flexible Time Intervals**: Supports various timeframes like `1h`, `4h`, `1d` (default), `1w`.
- **Candle-Count Based Charts**: Generates charts with a fixed number of candles (e.g., 150) for consistent analysis across different time intervals, rather than a fixed date range.
- **AI-Powered Analysis**: Leverages the DeepSeek API to generate a narrative analysis based on the chart and key data points.
- **Robust Architecture**: A decoupled architecture where resource-intensive Playwright operations (charting, report rendering) are executed in isolated CLI scripts, avoiding common `asyncio` event loop conflicts with web servers like Uvicorn.

## Technology Stack

- **Backend**: Python 3.11 with FastAPI
- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Data Source**: OpenBB SDK with Financial Modeling Prep (FMP) as the provider.
- **Chart Rendering**: Playwright & TradingView Lightweight Charts
- **AI Analysis**: DeepSeek API (via the `openai` library)
- **Dependency Management**: `uv`

---

## Setup and Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/Archerouyang/project_alpha.git
    cd project_alpha
    ```

2.  **Create and Activate Virtual Environment**:
    This project uses `uv` for fast dependency management.
    ```bash
    # Install uv if you haven't already
    pip install uv

    # Create and activate the virtual environment
    uv venv
    source .venv/bin/activate  # On Windows, use: .\.venv\Scripts\Activate.ps1
    ```

3.  **Install Dependencies**:
    The `--prerelease=allow` flag is currently required to resolve a dependency conflict with OpenBB.
    ```bash
    uv pip install -r requirements.txt --prerelease=allow
    ```

4.  **Set Up API Keys**:
    - Create a file named `.env` in the root of the project directory.
    - Add your DeepSeek and Financial Modeling Prep (FMP) API keys to the file:
      ```env
      DEEPSEEK_API_KEY="your_deepseek_api_key"
      FMP_API_KEY="your_fmp_api_key"
      ```
    - The `FMP_API_KEY` is required for fetching all market data.
    - The `DEEPSEEK_API_KEY` is required for the AI analysis portion.

---

## How to Run the Service

The application is run as a web server using Uvicorn.

1.  **Ensure your virtual environment is activated.**
2.  **Start the server from the project root directory**:
    ```bash
    uvicorn main:app --reload
    ```
3.  **Open your browser** and navigate to `http://127.0.0.1:8000`.

## How to Use the Interface

Enter your request in the input box using the following format:

**`[TICKER] [EXCHANGE?(Optional)] [INTERVAL?(Optional)]`**

-   **TICKER**: The stock symbol or crypto pair (e.g., `AAPL`, `BTC-USD`).
-   **EXCHANGE**: (Optional) The crypto exchange (e.g., `KRAKEN`, `BINANCE`). Omit for stocks.
-   **INTERVAL**: (Optional) The time interval (e.g., `1h`, `4h`, `1d`, `1w`). Defaults to `1d`.

**Examples:**
- `TSLA 4h`
- `BTC-USD KRAKEN 1h`
- `NVDA` 