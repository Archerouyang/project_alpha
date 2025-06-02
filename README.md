# Project Alpha: AI Technical Analysis Service

Project Alpha is an open-source service that provides AI-powered technical analysis for stocks.

Users can input a stock code, and the system will:
1. Fetch recent K-line data (1-hour intervals over the last 20 days).
2. Generate a K-line chart image with pre-set technical indicators using TradingView Lightweight Charts™.
3. Analyze the chart image using a multimodal LLM (e.g., Gemini Pro Vision, GPT-4V) via LangChain.
4. Produce a technical analysis report.

## Features (MVP)

- Input stock code via a simple web interface.
- Fetch 1-hour K-line data for the last 20 days.
- Generate chart images (backend or headless browser).
- LLM-based analysis of chart images.
- Output report (Markdown, image, or simple HTML).

## Tech Stack

- **Frontend Charting**: TradingView Lightweight Charts™
- **Backend Framework**: Python (FastAPI planned)
- **LLM Interaction**: LangChain (Python)
- **Data Fetching**: yfinance (or similar)
- **Package Management**: uv
- **Optional (Chart Generation)**: Playwright/Puppeteer if using headless browser

## Folder Structure

```
project_alpha/
├── .gitignore
├── pyproject.toml
├── README.md
├── backend/
│   ├── app/
│   │   ├── core/
│   │   └── main.py
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── schemas.py
│   └── services/
│       ├── chart_generator/
│       │   └── templates/
│       ├── data_fetcher/
│       ├── llm_agent/
│       │   └── prompts/
│       └── report_generator/
├── config/
├── frontend/
│   ├── css/
│   └── js/
├── scripts/
├── utils/
├── docs/
├── tests/
└── generated_reports/
```

For a detailed explanation of the folder structure, see [docs/architecture.md](docs/architecture.md) (to be created).

## Getting Started

### Prerequisites

- Python 3.9+
- uv (Python package installer and virtual environment manager)
- Access to an LLM API (e.g., OpenAI, Google AI Studio) and an API key.

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Archerouyang/project_alpha.git
    cd project_alpha
    ```

2.  **Create a virtual environment and install dependencies using uv:**
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    uv pip install -r requirements.txt # Or 'uv pip install .' if pyproject.toml is fully configured
    ```
    *(Note: `uv pip install .` will use the `pyproject.toml` directly. If you prefer a `requirements.txt`, you can generate one using `uv pip freeze > requirements.txt` after installing dependencies initially listed in `pyproject.toml`)*

3.  **Configure API Keys:**
    *   Create a `.env` file in the `config/` directory by copying `config/.env.example` (you'll need to create this example file).
    *   Add your LLM API key (e.g., `OPENAI_API_KEY="your_key_here"`) and any other necessary configurations to `.env`.
    Example `config/.env.example`:
    ```
    # LLM Configuration
    # OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    # GEMINI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    # Data Fetcher Configuration
    # ALPHA_VANTAGE_API_KEY="xxxxxxxxxxxxxxxx"
    ```

### Running the Development Server (FastAPI)

Once the backend is set up (see `backend/app/main.py`):

```bash
uv run dev
```

This will typically start the server at `http://127.0.0.1:8000`.

## MVP Local Execution (Alternative)

For quick testing or if the web UI is not yet complete, you might use a script:

```bash
python scripts/run_pipeline_local.py --stock AAPL
```

## Contributing

Contributions are welcome! Please read the `CONTRIBUTING.md` (to be created) for guidelines on how to contribute to this project.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the Apache-2.0 License. See `LICENSE` for more information. 