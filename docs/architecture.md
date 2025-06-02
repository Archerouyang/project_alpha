# Project Alpha: Folder Structure

This document outlines the folder structure for Project Alpha, an AI Technical Analysis Service.

```
project_alpha/
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
│
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application, API routes
│   ├── core/
│   │   ├── __init__.py
│   │   ├── chart_generator.py # Logic for generating charts (e.g., with Playwright)
│   │   ├── llm_agent.py       # LangChain logic for LLM interaction
│   │   ├── data_fetcher.py    # Fetches stock data (e.g., from yfinance)
│   │   └── report_service.py  # Orchestrates the analysis and prepares report data
│   ├── models/                # Pydantic models for API request/response validation
│   │   ├── __init__.py
│   │   └── schemas.py         # Defines data shapes (e.g., StockInput, ReportOutput)
│   └── templates/             # Optional: For any server-side HTML snippets
│       └── .gitkeep
│
├── config/
│   ├── __init__.py
│   ├── settings.py          # Loads .env and provides typed configuration settings
│   ├── .env                 # Stores API keys, sensitive data (should be in .gitignore)
│   └── .env.example         # Example structure for .env file
│
├── frontend/
│   ├── index.html           # Main HTML page for user interaction
│   └── static/              # For static assets
│       ├── css/
│       │   └── style.css    # CSS styles for the frontend
│       └── js/
│           └── app.js       # JavaScript for frontend logic (API calls, DOM manipulation)
│
├── scripts/                 # Auxiliary scripts (e.g., one-off tasks, deployment)
│   ├── __init__.py
│   └── .gitkeep
│
├── utils/                   # Shared utility functions and constants
│   ├── __init__.py
│   └── helpers.py           # Common helper functions used across the project
│
├── docs/                    # Project documentation (this file is here!)
│   ├── architecture.md
│   └── .gitkeep
│
└── generated_reports/       # To store generated images/reports locally (usually gitignored)
    └── .gitkeep
```

## Key Directory Explanations

*   **`project_alpha/` (Root Directory)**: Contains global project files like `pyproject.toml`, `README.md`, `.gitignore`, and `requirements.txt`.

*   **`backend/`**: Houses all Python code for the FastAPI backend API and core logic.
    *   `main.py`: FastAPI application instantiation, global middleware, and API router inclusions.
    *   `core/`: Contains the main business logic modules:
        *   `chart_generator.py`: Generates K-line chart images using TradingView Lightweight Charts (likely via a headless browser like Playwright).
        *   `llm_agent.py`: Manages LangChain setup, prompt engineering, and interaction with multimodal LLMs.
        *   `data_fetcher.py`: Retrieves stock K-line data from external APIs (e.g., yfinance).
        *   `report_service.py`: Orchestrates the overall process from receiving a stock code to returning an analysis report. It coordinates calls to `data_fetcher`, `chart_generator`, and `llm_agent`.
    *   `models/schemas.py`: Defines Pydantic models for API request and response data validation and serialization.
    *   `templates/`: Directory for any server-side rendered HTML templates or snippets, if needed.

*   **`config/`**: Manages application configuration.
    *   `settings.py`: A Python module to load configuration variables from environment variables (via `.env`) or other sources, providing them as typed settings.
    *   `.env`: Stores sensitive API keys and environment-specific configurations. This file is listed in `.gitignore` and should not be committed to the repository.
    *   `.env.example`: An example template for the `.env` file, showing required variables.

*   **`frontend/`**: Contains all files for the client-side web interface.
    *   `index.html`: The main HTML file that users interact with.
    *   `static/`: Subdirectory for static assets.
        *   `css/style.css`: CSS stylesheets.
        *   `js/app.js`: Client-side JavaScript for handling user input, making API calls to the backend, and dynamically updating the page with results (chart image and analysis text).

*   **`scripts/`**: For utility or maintenance scripts not part of the main application flow (e.g., deployment scripts, data migration scripts).

*   **`utils/helpers.py`**: Contains shared utility functions or constants that can be used across different parts of the project (both backend and potentially scripts).

*   **`docs/`**: Project documentation files.
    *   `architecture.md`: This file, detailing the folder structure and component overview.

*   **`generated_reports/`**: A directory (typically gitignored) where generated chart images or reports might be temporarily stored or cached by the backend if needed.

This structure aims for clarity, modularity, and ease of navigation, supporting the MVP goals while allowing for future expansion. 