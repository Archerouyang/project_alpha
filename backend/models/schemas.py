from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Any

class StockInput(BaseModel):
    stock_code: str

class ReportData(BaseModel):
    stock_code: str
    chart_image_url: Optional[str] = None # Could be a URL or a base64 encoded string path
    # If base64, frontend might need to know. Consider a flag or prefix.
    analysis_text: str

class AnalysisReportResponse(BaseModel):
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[ReportData] = None

# Example for K-line data points if you were to type them strictly
# class KlinePoint(BaseModel):
#     timestamp: Any # or datetime
#     open: float
#     high: float
#     low: float
#     close: float
#     volume: int

# class StockDataResponse(BaseModel):
#     stock_code: str
#     kline_data: List[KlinePoint]
#     error: Optional[str] = None 