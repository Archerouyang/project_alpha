from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import io # For BytesIO

from backend.core.chart_generator import LightweightChartGenerator
# Assuming schemas.py might be used later for request/response models
# from backend.models import schemas 

# Initialize the chart generator. 
# It can be initialized once and reused if its state is not request-specific,
# or initialized per request if necessary (e.g., if output_dir needs to change).
# For now, let's initialize it globally as its config is static.
chart_gen = LightweightChartGenerator() 

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
async def analyze_stock(stock_code: str = Query(..., description="Stock ticker symbol, e.g., AAPL or BTC-USD")):
    # This will eventually call the report_service
    return {"stock_code": stock_code, "status": "analysis_pending", "message": "Full analysis endpoint is a work in progress."}

@app.get("/api/chart/generate/{ticker_symbol}", 
         response_class=StreamingResponse, 
         summary="Generate Stock Chart Image",
         description="Generates a K-line chart image for the given ticker symbol with MA, MACD, RSI, and Bollinger Bands.")
async def generate_chart_api(
    ticker_symbol: str,
    days: int = Query(20, description="Number of past days for the chart data", ge=5, le=365),
    interval: str = Query("1h", description="Data interval (e.g., 1m, 15m, 1h, 1d)")
):
    """
    Endpoint to generate and return a stock chart image.
    - **ticker_symbol**: The stock or crypto symbol (e.g., AAPL, BTC-USD).
    - **days**: Number of past days of data to display on the chart (min 5, max 365).
    - **interval**: Data interval. Common ones: 1m, 5m, 15m, 1h, 1d.
                      (Refer to yfinance for exact supported intervals like 1wk, 1mo).
    """
    try:
        print(f"API call to generate chart for {ticker_symbol}, days={days}, interval={interval}")
        image_bytes_io = await chart_gen.generate_chart_image(
            ticker_symbol=ticker_symbol,
            days=days,
            interval=interval,
            return_bytes=True
        )

        if image_bytes_io is None:
            print(f"Chart generation failed for {ticker_symbol}, image_bytes_io is None.")
            raise HTTPException(status_code=500, detail=f"Chart generation failed for {ticker_symbol}. Could not fetch data or render chart.")

        image_bytes_io.seek(0) # Reset stream position to the beginning
        
        print(f"Successfully generated chart for {ticker_symbol}. Returning image stream.")
        return StreamingResponse(image_bytes_io, media_type="image/png")

    except HTTPException as http_exc: # Re-raise HTTPException
        raise http_exc 
    except Exception as e:
        print(f"An unexpected error occurred during chart generation for {ticker_symbol}: {e}")
        # Log the full exception for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred while generating the chart for {ticker_symbol}.")

# To run this app (from the project_alpha directory):
# Ensure .venv is activated: source .venv/bin/activate (or .venv\Scripts\activate on Windows)
# Then run: uvicorn backend.main:app --reload 