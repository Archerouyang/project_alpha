# AI-Powered Stock Analysis Service (WeChat Mini Program Edition)

This project provides a sophisticated financial analysis service, now re-architected for WeChat. It allows users to get AI-powered technical analysis reports for stocks and cryptocurrencies directly within a WeChat Mini Program.

The system's backend fetches market data, generates detailed candlestick charts, uses a Large Language Model (LLM) for in-depth analysis, and serves the final report to the WeChat client.

## Architecture: Cloud Backend + Mini Program Frontend

To support WeChat, the project has transitioned from a monolithic web server to a decoupled, cloud-native architecture.

-   **Backend (Cloud API Service)**
    -   A **FastAPI (Python)** application that exposes endpoints for instruction validation and report generation.
    -   This service is designed to be deployed to a **cloud server** (e.g., AWS, Azure, Heroku, or similar) and must be accessible via a public HTTPS URL.
    -   It continues to use OpenBB for data, Playwright for charting, and DeepSeek for AI analysis.

-   **Frontend (WeChat Mini Program)**
    -   A new frontend built specifically for the WeChat environment, located in the `/miniprogram` directory.
    -   It uses WeChat's native components (`WXML`, `WXSS`) for the user interface.
    -   Client-side logic is written in JavaScript and communicates with the backend via `wx.request()` API calls.

## Project Roadmap for Mini Program Migration

This README outlines the development plan to complete the migration.

-   [ ] **1. Deploy Backend to Cloud**: Package and deploy the existing FastAPI application to a public cloud server, obtaining a stable HTTPS API endpoint.
-   [ ] **2. Initialize Mini Program Project**: Create the basic file structure (`/miniprogram` directory) for a new WeChat Mini Program.
-   [ ] **3. Rebuild UI in WXML/WXSS**: Recreate the chat-based user interface using WeChat's native UI language.
-   [ ] **4. Implement Client Logic**:
    -   Rewrite the JavaScript logic to handle user input.
    -   Replace `fetch` calls with `wx.request` to communicate with the deployed backend.
    -   Manage state and display results (loading indicators, AI messages, report images).
-   [ ] **5. Configuration & Testing**: Configure the backend API URL in the mini program and conduct end-to-end testing in the WeChat Developer Tools.

---

## Setup and Development

This section describes how to set up the two parts of the project for development.

### 1. Backend API Service

The backend setup remains largely the same.

1.  **Clone, Create Virtual Env, Install Dependencies**: Follow the original setup steps using `uv`.
    ```bash
    # Install dependencies
    uv pip install -r requirements.txt --prerelease=allow
    ```
2.  **Set Up API Keys**: Create a `.env` file in the project root with your `DEEPSEEK_API_KEY` and `FMP_API_KEY`.
3.  **Run Locally for Development**:
    ```bash
    uvicorn main:app --reload
    ```
    During development, the backend will run on `http://127.0.0.1:8000`. You will need to configure your WeChat Developer Tools to allow requests to this local address.

### 2. Frontend WeChat Mini Program

1.  **Install WeChat Developer Tools**: Download and install the official [WeChat Developer Tools](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html).
2.  **Import the Project**:
    -   Open the developer tools and choose to import a project.
    -   Point the project directory to the `project_alpha` folder (or wherever you cloned the repo).
    -   Set the "AppID" for your mini program. If you don't have one, you can use a test AppID provided by the tools.
    -   The tools should automatically detect the `miniprogram` folder (once we create it).
3.  **Configure API Endpoint**:
    -   Inside the mini program's code, you will need to set the backend URL to point to your deployed service (for production) or your local machine (for development).

---

## Technology Stack

-   **Backend**: Python 3.11 with FastAPI
-   **Frontend**: WeChat Mini Program (WXML, WXSS, JavaScript)
-   **Data Source**: OpenBB SDK
-   **Chart Rendering**: Playwright & TradingView Lightweight Charts
-   **AI Analysis**: DeepSeek API
-   **Deployment**: Cloud Server (Heroku, Vercel, AWS, etc.)

## Features

- **Web UI**: A clean, chat-like interface to request and display analysis reports.
- **Equity and Crypto Support**: Intelligently fetches data for both stock tickers (e.g., `AAPL`) and cryptocurrency pairs (e.g., `BTC-USD`).
- **Exchange-Specific Data**: Allows specifying a cryptocurrency exchange (e.g., `KRAKEN`, `BINANCE`) for precise data sourcing.
- **Flexible Time Intervals**: Supports various timeframes like `1h`, `4h`, `1d` (default), `1w`.
- **Candle-Count Based Charts**: Generates charts with a fixed number of candles (e.g., 150) for consistent analysis across different time intervals, rather than a fixed date range.
- **AI-Powered Analysis**: Leverages the DeepSeek API to generate a narrative analysis based on the chart and key data points.
- **Robust Architecture**: A decoupled architecture where resource-intensive Playwright operations (charting, report rendering) are executed in isolated CLI scripts, avoiding common `asyncio` event loop conflicts with web servers like Uvicorn.

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