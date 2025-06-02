from fastapi import FastAPI
from contextlib import asynccontextmanager

# Placeholder for lifespan events (e.g., startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    print("Application startup...")
    # You could initialize resources here, like DB connections, ML models, etc.
    yield
    # Clean up the ML model and release the resources
    print("Application shutdown...")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"message": "Welcome to Project Alpha - AI Technical Analysis Service"}

# Placeholder for the main analysis endpoint
@app.post("/api/analyze/")
async def analyze_stock(stock_code: str):
    # This will eventually call the report_service
    # For now, a placeholder response
    return {"stock_code": stock_code, "status": "analysis_pending"}

# To run this app (from the project_alpha directory):
# Ensure .venv is activated: source .venv/bin/activate (or .venv\Scripts\activate on Windows)
# Then run: uvicorn backend.main:app --reload 