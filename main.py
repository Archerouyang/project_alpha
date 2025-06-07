import base64
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file.
# This should be at the top to ensure they are loaded for all modules.
load_dotenv()

# With main.py at the root, we no longer need to manipulate sys.path.
# Python and Uvicorn will handle it correctly.
from backend.core.orchestrator import AnalysisOrchestrator

app = FastAPI()

# --- Pydantic Models ---
class AnalysisRequest(BaseModel):
    ticker: str
    interval: str
    num_candles: int = 150
    exchange: Optional[str] = None

class AnalysisResponse(BaseModel):
    image: str

class InstructionValidationRequest(BaseModel):
    user_input: str

class InstructionValidationResponse(BaseModel):
    status: str  # "valid", "corrected", "clarification_needed"
    command: Optional[str] = None
    explanation: Optional[str] = None

# --- Static Files & Frontend Serving ---
# Paths are now relative to the project root where main.py is located.
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML file."""
    return FileResponse("frontend/index.html")

# --- API Endpoints ---
@app.post("/api/validate_instruction", response_model=InstructionValidationResponse)
async def validate_instruction(request: InstructionValidationRequest):
    """
    Validates, corrects, or asks for clarification on a user's instruction using an LLM.
    """
    # This is a placeholder. We will implement the actual logic in a new module.
    # For now, let's simulate a "valid" response for testing.
    from backend.core.instruction_validator import validate_and_extract_command
    
    response = await validate_and_extract_command(request.user_input)
    return response

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    print(f"Received analysis request for: {request.ticker} on exchange {request.exchange or 'default'} ({request.interval})")
    try:
        orchestrator = AnalysisOrchestrator()
        
        final_report_path, error = await orchestrator.generate_report(
            ticker=request.ticker,
            interval=request.interval,
            num_candles=request.num_candles,
            exchange=request.exchange
        )
        
        if error:
            print(f"An error occurred: {error}")
            raise HTTPException(status_code=500, detail=f"Report generation failed: {error}")

        if not final_report_path or not os.path.exists(final_report_path):
            print(f"An error occurred: Final report image not found at {final_report_path}")
            raise HTTPException(status_code=500, detail="Report generation failed: Final report image not found.")

        with open(final_report_path, "rb") as image_file:
            image_base64_str = base64.b64encode(image_file.read()).decode("utf-8")

        return AnalysisResponse(image=image_base64_str)
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"An unexpected error occurred in /api/analyze: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")

# To run this app (from the project_alpha directory):
# Ensure .venv is activated: source .venv/bin/activate (or .venv\Scripts\activate on Windows)
# Then run: uvicorn backend.main:app --reload 