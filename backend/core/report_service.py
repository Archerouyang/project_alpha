# backend/core/report_service.py

from .data_fetcher import get_stock_data
from .chart_generator import generate_chart_image
from .llm_agent import analyze_image_with_llm
# from backend.models.schemas import AnalysisReport # Assuming you have this Pydantic model

async def create_analysis_report(stock_code: str) -> dict: # Replace dict with AnalysisReport later
    """
    Orchestrates the creation of a technical analysis report.
    1. Fetches stock data.
    2. Generates a chart image from the data.
    3. Sends the chart image to an LLM for analysis.
    4. Compiles the results into a report.

    Args:
        stock_code (str): The stock code to analyze.

    Returns:
        dict: A dictionary containing the report (chart image URL/data and analysis text).
              Should be replaced with a Pydantic model like AnalysisReport.
    """
    print(f"Creating analysis report for {stock_code}...")

    # 1. Fetch data
    stock_data_df = await get_stock_data(stock_code)
    if stock_data_df.empty:
        return {"error": f"Could not fetch data for {stock_code}"}
    
    # Convert DataFrame to dict for chart generator (example, adjust as needed)
    # The chart_generator will need a specific format, e.g., a list of OHLCV dicts
    # For simplicity, passing the DataFrame; chart_generator would need to handle it.
    chart_input_data = stock_data_df.to_dict(orient="records") 
    # You might need to process timestamps to be JSON serializable if they are not already strings
    # For example: chart_input_data = stock_data_df.reset_index().to_dict(orient="records")
    # and ensure DateTimeIndex is handled (e.g. df.index = df.index.strftime('%Y-%m-%d %H:%M:%S'))

    # 2. Generate chart image
    # Pass stock_data_df or a processed version to generate_chart_image
    chart_image_ref = await generate_chart_image(stock_code, data=chart_input_data) # type: ignore
    if not chart_image_ref:
        return {"error": f"Could not generate chart for {stock_code}"}

    # 3. Analyze image with LLM
    analysis_text = await analyze_image_with_llm(chart_image_ref, stock_code)
    if not analysis_text:
        return {"error": f"Could not analyze chart image for {stock_code}"}

    # 4. Compile report
    report = {
        "stock_code": stock_code,
        "chart_image_url": chart_image_ref, # This might be a URL or base64 data
        "analysis_text": analysis_text
    }
    
    print(f"Report created successfully for {stock_code}.")
    # return AnalysisReport(**report) # If using Pydantic model
    return report 