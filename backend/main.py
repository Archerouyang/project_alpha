import base64
import os
import sys
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file at the very top
# This ensures all modules and subprocesses can access them.
load_dotenv()

# Add project root to path to allow imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.core.orchestrator import AnalysisOrchestrator

# --- Pydantic Models ---
class AnalyzeRequest(BaseModel):
    ticker: str
    interval: str = "1d"
    num_candles: int = 150 # Changed from days to num_candles
    exchange: str | None = None
    language: str | None = Field(default="English", alias="language")

class AnalyzeResponse(BaseModel):
    image_base64: str
    analysis_text: str

# --- FastAPI App Initialization ---
app = FastAPI(
    title="AI Technical Analysis Service",
    description="An API for generating technical analysis reports for stock tickers.",
)

# --- CORS Configuration ---
# This is crucial for allowing the frontend to communicate with the backend
# when they are served on different ports (e.g., frontend on 8000, backend on 8001).
origins = [
    "http://localhost",
    "http://localhost:8000", # Default port for `python -m http.server`
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods
    allow_headers=["*"], # Allow all headers
)

# --- API Endpoints ---
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_stock(request: AnalyzeRequest):
    """
    This endpoint receives a stock symbol and other optional parameters,
    runs the analysis orchestrator, and returns the report.
    """
    print(f"Received analysis request for: {request.ticker} ({request.interval})")
    try:
        orchestrator = AnalysisOrchestrator()
        
        final_report_path, error = await orchestrator.generate_report(
            ticker=request.ticker,
            interval=request.interval,
            num_candles=request.num_candles
        )
        
        if error:
            print(f"An error occurred: {error}")
            raise HTTPException(status_code=500, detail=f"Report generation failed: {error}")

        if not final_report_path or not os.path.exists(final_report_path):
            print(f"An error occurred: Final report image not found at {final_report_path}")
            raise HTTPException(status_code=500, detail="Report generation failed: Final report image not found.")

        # The orchestrator now returns the final report image path directly.
        # The analysis markdown is an intermediate file in the same directory.
        analysis_md_path = os.path.join(os.path.dirname(final_report_path), "analysis.md")

        with open(final_report_path, "rb") as image_file:
            image_base64_str = base64.b64encode(image_file.read()).decode("utf-8")

        analysis_text = ""
        if os.path.exists(analysis_md_path):
             with open(analysis_md_path, "r", encoding="utf-8") as text_file:
                analysis_text = text_file.read()
        else:
            print(f"Warning: analysis.md file not found at {analysis_md_path}")

        image_data_url = f"data:image/png;base64,{image_base64_str}"
        
        return AnalyzeResponse(
            image_base64=image_data_url,
            analysis_text=analysis_text,
        )
    except HTTPException as http_exc:
        # Re-raise HTTPException to let FastAPI handle it
        raise http_exc
    except Exception as e:
        print(f"An unexpected error occurred in /api/analyze: {e}")
        # Log the full traceback for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")

# --- Serving Frontend ---
# This mounts the 'frontend' directory, allowing FastAPI to serve the static files.
# This is an alternative to running a separate python http.server.
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML file."""
    html_file_path = os.path.join(project_root, "frontend", "index.html")
    if not os.path.exists(html_file_path):
        return HTMLResponse(content="<h1>Index.html not found!</h1>", status_code=404)
    return FileResponse(html_file_path)

# To run this app (from the project_alpha directory):
# Ensure .venv is activated: source .venv/bin/activate (or .venv\Scripts\activate on Windows)
# Then run: uvicorn backend.main:app --reload 