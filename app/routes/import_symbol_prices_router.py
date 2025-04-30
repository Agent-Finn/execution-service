from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..service.import_symbol_prices import import_symbol_prices_from_csv
import os

router = APIRouter(
    prefix="/symbol-prices",
    tags=["Symbol Prices"]
)

class ImportResponse(BaseModel):
    status: str
    total_processed: Optional[int] = None
    successfully_imported: Optional[int] = None
    already_exists: Optional[int] = None
    errors: Optional[int] = None
    error_details: Optional[list] = None
    message: Optional[str] = None

@router.post("/import-csv", response_model=ImportResponse)
async def import_symbol_prices():
    """
    Import historical ticker prices from the SPY.csv file into the symbol_prices table.
    
    This endpoint:
    1. Reads the SPY.csv file
    2. For each row, it:
       - Gets the symbol_id from symbols table
       - Uses the open price as the price value
       - Uses the date as price_at value
    3. Adds the data to symbol_prices table
    
    Returns:
        ImportResponse: Details of the import operation
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Define the path to the CSV file
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'SPY.csv')
        
        # Check if the file exists
        if not os.path.exists(csv_path):
            raise HTTPException(
                status_code=404,
                detail=f"CSV file not found at {csv_path}"
            )
        
        # Import the data
        result = await import_symbol_prices_from_csv(csv_path)
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
            
        return result
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error importing symbol prices: {str(e)}"
        ) 