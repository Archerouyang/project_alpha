# AI-Powered Financial Analysis Service

[![Status](https://img.shields.io/badge/Status-Fully%20Functional-brightgreen.svg)](https://github.com/Archerouyang/project_alpha)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)](https://fastapi.tiangolo.com/)
[![Cache](https://img.shields.io/badge/Cache-Smart%20Optimized-orange.svg)](https://github.com/Archerouyang/project_alpha)

This project provides a sophisticated financial analysis service, accessible via a clean, web-based chat interface. It allows users to get AI-powered technical analysis reports for stocks and cryptocurrencies, which are presented in a polished, professional, and easy-to-read image format.

The system's backend fetches market data, generates detailed candlestick charts, uses a Large Language Model (LLM) for in-depth analysis, and composites the chart and text into a final, beautifully designed report image.

**🚀 NEW: Smart Caching System**: Revolutionary multi-layer caching reduces response time from 26s to 1-3s (88% improvement) for repeated requests. Features intelligent TTL policies, LRU memory management, and comprehensive performance monitoring.

**✅ Recently Fixed**: Data fetching compatibility issues and chart generation problems have been resolved. The system now includes robust fallback mechanisms for reliable operation.

---

## Current Features

-   **🚀 Smart Caching System**: Revolutionary multi-layer intelligent caching dramatically improves performance:
    -   **Dual-layer Architecture**: Memory cache + disk cache for optimal speed and persistence
    -   **Intelligent TTL Policies**: Data (5min), Charts (10min), AI Analysis (30min)
    -   **Performance Gains**: 88% response time reduction (26s → 1-3s for cached requests)
    -   **LRU Memory Management**: Automatic cleanup with configurable limits
    -   **Thread-Safe Design**: Concurrent request handling with data consistency

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
-   **Smart Caching**: Multi-layer cache system with TTL policies and LRU eviction
-   **Performance Monitoring**: Real-time tracking with detailed analytics
-   **Data Source**: OpenBB SDK with FMP API provider + Direct FMP API fallback
-   **Chart Rendering**: Playwright & TradingView Lightweight Charts (Windows: Chromium, Docker: Firefox)
-   **AI Analysis**: DeepSeek API
-   **Dependency Management**: uv

---

## Quick Start

For a rapid setup, follow these essential steps:

1. **Clone & Setup Environment**:
   ```bash
   git clone <your-repository-url>
   cd project_alpha
   uv venv && .venv\Scripts\activate
   uv pip install -r requirements.txt --prerelease=allow
   ```

2. **Configure API Keys** - Create `.env` file:
   ```env
   DEEPSEEK_API_KEY="your_deepseek_api_key"
   FMP_API_KEY="your_fmp_api_key"
   ```

3. **Install Browser & Start**:
   ```bash
   playwright install chromium
   uvicorn main:app --reload
   ```

4. **Test**: Open `http://127.0.0.1:8000` and try `NVDA` or `BTC-USD`

---

## 🚀 Performance Optimization

### Smart Caching System

Our revolutionary multi-layer caching system delivers unprecedented performance improvements:

| Component | First Request | Cached Request | Improvement |
|-----------|---------------|----------------|-------------|
| **Data Fetch** | 1.5s | 0.1s | **93%** |
| **Chart Generation** | 20s | 0.5s | **97%** |
| **AI Analysis** | 3s | 0.1s | **97%** |
| **Total Response** | **26s** | **1-3s** | **88%** |

### Cache Management API

Monitor and control the caching system via API endpoints:

```bash
# Get cache statistics
GET /api/cache/stats

# Clear expired cache entries
POST /api/cache/clear

# Clear all cache (development)
DELETE /api/cache/all

# Performance monitoring
GET /api/performance/stats
GET /api/performance/report

# System health check
GET /api/health
```

### Performance Testing

Run comprehensive cache performance tests:

```bash
# Execute performance tests
python tests/test_cache_performance.py

# Results show dramatic improvements:
# ✅ Average performance improvement: 85%+
# ⚡ Average speedup factor: 10x+
# 🎯 Cache hit rates: 80-95%
```

### Cache Configuration

Customize caching behavior in `config/cache_config.yaml`:

```yaml
cache:
  enabled: true
  data_ttl: 300      # 5 minutes - market data
  chart_ttl: 600     # 10 minutes - chart images  
  analysis_ttl: 1800 # 30 minutes - AI analysis
  max_memory_entries: 1000
  max_disk_size_mb: 500
```

---

## Detailed Setup and Run

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

3.  **Set Up API Keys**: Create a `.env` file in the project root with your API keys.
    ```env
    # .env - API Configuration
    DEEPSEEK_API_KEY="your_deepseek_api_key_here"
    FMP_API_KEY="your_financial_modeling_prep_api_key_here"
    
    # Optional configuration
    DEBUG=false
    APP_NAME="Project Alpha AI Technical Analysis Service"
    TRADINGVIEW_CHART_WIDTH=1200
    TRADINGVIEW_CHART_HEIGHT=800
    ```
    
    **Getting API Keys:**
    - **DeepSeek API**: Sign up at [DeepSeek](https://platform.deepseek.com/) for AI analysis
    - **FMP API**: Get a free key at [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs) for market data

4.  **Install Playwright Browsers**: Required for chart generation.
    ```bash
    # Install Playwright browsers (required for chart rendering)
    playwright install chromium
    
    # Alternatively, install all browsers
    playwright install
    ```

5.  **Run the Web Server**:
    ```bash
    uvicorn main:app --reload
    ```

6.  **Access the Service**: Open your browser and navigate to `http://127.0.0.1:8000`.

## Docker Deployment

### Build and Push Docker Image 📦

1. Ensure Docker is installed locally and you are logged in to Docker Hub.
2. Build the image:
   ```bash
   docker build -t archerouyang/project-alpha:latest .
   ```
3. Push to Docker Hub:
   ```bash
   docker push archerouyang/project-alpha:latest
   ```

### Deploy on Alibaba Cloud ECS ☁️

1. SSH into your ECS instance:
   ```bash
   ssh root@<ECS_IP>
   ```
2. Pull the image:
   ```bash
   docker pull archerouyang/project-alpha:latest
   ```
3. Run the container:
   ```bash
   docker run -d -p 8000:8000 \
     --name project-alpha-container \
     archerouyang/project-alpha:latest
   ```
4. Confirm it's running:
   ```bash
   docker ps -a
   ```
5. Access via `http://<ECS_IP>:8000` or use SSH 隧道：
   ```bash
   ssh -L 8000:127.0.0.1:8000 root@<ECS_IP>
   ```
   then open `http://localhost:8000`.

🔒 **HTTPS & Custom Domain**  
After your domain verification, configure Nginx reverse proxy and Let's Encrypt certificate for `https://your-domain.com`.

---

## Data Management

- Initialize the reports database:
  ```bash
  python backend/db/init_reports_db.py
  ```
- View historical reports via HTTP API:
  ```bash
  curl http://<HOST>/api/analysis/history?user_id=<USER_ID>&date=YYYY-MM-DD
  ```
- Clean up expired reports (default keep 7 days):
  ```bash
  python scripts/cleanup_reports.py [days_to_keep]
  ```
- SQLite database file: `backend/db/reports.db`

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

## Troubleshooting

### Data Fetching Issues
- **OpenBB Import Error**: If you encounter `cannot import name 'OBBject_EquityInfo'` errors, the system will automatically fall back to direct FMP API calls. This is a known compatibility issue with certain OpenBB versions.
- **FMP API Key**: Ensure your `FMP_API_KEY` is correctly set in the `.env` file. You can get a free API key from [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs).

### Chart Generation Issues
- **Playwright Browser Missing**: If you see `Executable doesn't exist` errors, run `playwright install chromium` to install the required browser.
- **PowerShell Execution Policy (Windows)**: If you encounter PowerShell script execution issues, you can:
  - Use `.bat` files instead of `.ps1` scripts for virtual environment activation
  - Or set execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### API Configuration
- **DeepSeek API**: Ensure your `DEEPSEEK_API_KEY` is valid for AI analysis functionality.
- **Environment Variables**: The system automatically loads API keys from the `.env` file. Restart the server after making changes to `.env`.

### Cache and Performance Issues
- **Cache Not Working**: If cache performance isn't improving response times:
  - Check cache configuration in `config/cache_config.yaml`
  - Verify cache directory permissions: `./cache_data`
  - Monitor cache stats via `/api/cache/stats` endpoint
  
- **Memory Usage High**: If experiencing high memory usage:
  - Reduce `max_memory_entries` in cache config
  - Clear cache manually: `POST /api/cache/clear`
  - Check disk cache size: `/api/health` endpoint
  
- **Cache Corruption**: If seeing cache-related errors:
  - Clear all cache: `DELETE /api/cache/all`
  - Restart the application
  - Check file system permissions for cache directory
  
- **Performance Monitoring**: 
  - View real-time stats: `GET /api/performance/stats`
  - Generate detailed report: `GET /api/performance/report`
  - Run performance tests: `python tests/test_cache_performance.py`

## Known Issues

- **Docker Environment**: Due to compatibility issues between Chromium and TradingView Lightweight Charts in Linux Docker containers, the Docker configuration uses Firefox for chart rendering. In Windows environments, Chromium is used by default.
- **OpenBB SDK Compatibility**: Some versions of OpenBB SDK may have import conflicts. The system includes automatic fallback to direct FMP API calls to ensure reliability. 