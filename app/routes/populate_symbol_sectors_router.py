from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from ..service.populate_symbol_sectors import populate_symbol_sectors

router = APIRouter(
    prefix="/populate-symbol-sectors",
    tags=["symbol_sectors"]
)

# Default symbols list from the user's request
DEFAULT_SYMBOLS = [
    "RL", "KMX", "DPZ", "GDDY", "ULTA", "WSM", "TSCO", "LULU", "NKE", "F",
    "SBUX", "COST", "WMT", "TGT", "PEP", "KO", "TSN", "DLTR", "XOM", "CVX",
    "PSA", "SPG", "CSGP", "PCG", "CEG", "D", "EXC", "DIS", "VZ", "T",
    "TMUS", "EA", "WBD", "MTCH", "V", "MA", "URI", "AXP", "BX", "DFS",
    "GRMN", "NDAQ", "TROW", "MCO", "CAT", "DAL", "DE", "BA", "ROST", "LMT",
    "UPS", "MMM", "FDX", "UAL", "LUV", "EFX", "SHW", "ECL", "DD", "DOW",
    "LLY", "UNH", "JNJ", "AMGN", "PFE", "CI", "CVS", "IDXX", "DGX", "MRNA",
    "MRK", "KR", "HUM", "COR", "GILD", "BBY", "FDS", "EL", "HSY", "KHC",
    "AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "ORCL", "CRM",
    "CSCO", "ADBE", "INTC", "IBM", "AMD", "QCOM", "NFLX", "TXN", "PYPL", "NOW"
]

class SymbolsRequest(BaseModel):
    symbols: Optional[List[str]] = None
    batch_size: Optional[int] = Field(default=5, ge=1, le=20, description="Number of symbols to process in each batch (Alpha Vantage has rate limits)")

@router.post("/", response_model=dict)
async def run_populate_symbol_sectors(data: Optional[SymbolsRequest] = None):
    """
    Populate symbol sectors table using Alpha Vantage API data.
    Note: Alpha Vantage has a rate limit of 5 calls per minute on the free tier.
    
    Args:
        data: Optional request body with list of symbols to process and batch size
        
    Returns:
        dict: Summary of the operation with counts of successes and failures
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        if data is None:
            data = SymbolsRequest()
        
        # Use provided symbols or fall back to the default list
        symbols_to_process = data.symbols if data.symbols else DEFAULT_SYMBOLS
        
        result = populate_symbol_sectors(symbols_to_process, batch_size=data.batch_size)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error populating symbol sectors: {str(e)}"
        ) 