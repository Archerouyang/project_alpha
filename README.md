# AI-Powered Financial Analysis Service

This project provides a sophisticated financial analysis service, accessible via a clean, web-based chat interface. It allows users to get AI-powered technical analysis reports for stocks and cryptocurrencies, which are presented in a polished, professional, and easy-to-read image format.

The system's backend fetches market data, generates detailed candlestick charts, uses a Large Language Model (LLM) for in-depth analysis, and composites the chart and text into a final, beautifully designed report image.

---

## Current Features

-   **Polished Report Generation**: Creates visually stunning report images based on a professional, modern template. Key design features include:
    -   A clean, card-based layout with a distinct header and footer.
    -   A "Key Data Dashboard" for at-a-glance metrics (e.g., close price, period high/low, indicator values).
    -   A sophisticated blue-gray and teal color scheme.
    -   Customizable author attribution with an avatar in the report footer.

-   **Intuitive Web UI**: A simple, chat-like interface to request and display analysis reports, running on FastAPI and Uvicorn.

-   **Broad Market Support**: Intelligently fetches data for both stock tickers (e.g., `AAPL`) and cryptocurrency pairs (e.g., `BTC-USD`).

-   **Exchange-Specific Data**: Allows specifying a cryptocurrency exchange (e.g., `KRAKEN`, `BINANCE`) for precise data sourcing.

-   **Flexible Time Intervals**: Supports various timeframes like `1h`, `4h`, `1d` (default), `1w`.

-   **AI-Powered Analysis**: Leverages the DeepSeek API to generate a narrative analysis based on the chart and key data points.

-   **Robust Architecture**: A decoupled architecture where resource-intensive Playwright operations (charting, report rendering) are executed in isolated CLI scripts, avoiding common `asyncio` event loop conflicts with web servers like Uvicorn.

---

## Project Structure

A brief overview of the key directories:

-   `backend/`: Contains the core application logic, including the FastAPI server, data fetching, analysis orchestration, and report generation.
-   `frontend/`: The static files (HTML, CSS, JS) for the web-based user interface.
-   `scripts/`: Holds standalone command-line scripts used by the orchestrator for heavy-lifting tasks like charting.
-   `assets/`: Stores static image assets, such as author avatars, used in report generation.
-   `generated_reports/`: The default output directory for the final report images.

---

## Technology Stack

-   **Backend**: Python 3.11 with FastAPI
-   **Frontend**: HTML, CSS, JavaScript
-   **Data Source**: OpenBB SDK
-   **Chart Rendering**: Playwright & TradingView Lightweight Charts
-   **AI Analysis**: DeepSeek API
-   **Dependency Management**: uv

---

## Setup and Run

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd project_alpha
    ```

2.  **Create Virtual Environment and Install Dependencies**: This project uses `uv` for package management.
    ```bash
    # Create a virtual environment
    uv venv
    
    # Activate the environment
    # On Windows
    .venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate

    # Install dependencies
    uv pip install -r requirements.txt --prerelease=allow
    ```

3.  **Set Up API Keys**: Create a `.env` file in the project root. You can copy the example below.
    ```env
    # .env
    DEEPSEEK_API_KEY="your_deepseek_api_key"
    FMP_API_KEY="your_financial_modeling_prep_api_key"
    ```

4.  **Run the Web Server**:
    ```bash
    uvicorn main:app --reload
    ```

5.  **Access the Service**: Open your browser and navigate to `http://127.0.0.1:8000`.

---

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

---

## Future Roadmap: WeChat Mini Program

The next major development phase for this project is to create a front-end client as a WeChat Mini Program, allowing users to access the service directly on their mobile devices.

### Planned Architecture

-   **Backend (Cloud API Service)**: The existing FastAPI application will be deployed to a public cloud server (e.g., AWS, Azure, Heroku) to provide a stable, public HTTPS API endpoint.
-   **Frontend (WeChat Mini Program)**: A new frontend will be built using WeChat's native technologies (WXML, WXSS, and JavaScript) to create a user experience optimized for mobile. It will communicate with the deployed backend via `wx.request()` API calls.

### Development Steps
-   [ ] **Deploy Backend to Cloud**: Package and deploy the FastAPI app.
-   [ ] **Initialize Mini Program Project**: Create the `/miniprogram` directory and basic file structure.
-   [ ] **Rebuild UI in WXML/WXSS**: Recreate the chat-based UI using WeChat's native components.
-   [ ] **Implement Client Logic**: Rewrite frontend logic in JavaScript for WeChat's environment.
-   [ ] **End-to-End Testing**: Configure the API endpoint and test thoroughly within WeChat Developer Tools. 