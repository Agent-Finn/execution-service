from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from ..service.backtest_allocations import run_backtest
import uuid

router = APIRouter(
    tags=["Backtesting"]
)

class BacktestRequest(BaseModel):
    portfolio_id: str = Field(..., description="UUID of the portfolio to backtest")
    allocation_dates: List[str] = Field(..., description="List of allocation dates in YYYY-MM-DD format")
    start_month: int = Field(1, ge=1, le=12, description="Month to start backtesting from (default: 1 for January)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "1ed7794b-b041-4d5e-8b0e-1730d66aaf0e",
                "allocation_dates": [
                    "2024-01-31", "2024-02-29", "2024-03-31", "2024-04-30", 
                    "2024-05-31", "2024-06-30", "2024-07-31", "2024-08-31", 
                    "2024-09-30", "2024-10-31", "2024-11-30", "2024-12-31"
                ],
                "start_month": 1
            }
        }

class BacktestResponse(BaseModel):
    status: str
    message: str
    results: Optional[List[Dict[str, Any]]] = None

@router.post("/run-backtest", response_model=BacktestResponse)
async def run_backtest_endpoint(backtest_request: BacktestRequest):
    """
    Run a full backtest for a portfolio across multiple months.
    
    For each month in the provided allocation dates (starting from start_month):
    1. Updates the portfolio balance for the month
    2. Gets the allocation_batch_id for the allocation date
    3. Plans a full trade using that allocation_batch_id
    
    The process continues sequentially, and stops if any step fails.
    
    Args:
        backtest_request (BacktestRequest): Contains portfolio_id, allocation_dates, and start_month
    
    Returns:
        BacktestResponse: Results of the backtest operation
    
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Validate UUID format for portfolio_id
        try:
            uuid.UUID(backtest_request.portfolio_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid portfolio_id: not a valid UUID"
            )
        
        # Validate allocation dates format (YYYY-MM-DD)
        for date in backtest_request.allocation_dates:
            try:
                year, month, day = date.split('-')
                if not (len(year) == 4 and len(month) == 2 and len(day) == 2):
                    raise ValueError()
                if not (int(month) >= 1 and int(month) <= 12):
                    raise ValueError()
                if not (int(day) >= 1 and int(day) <= 31):
                    raise ValueError()
            except (ValueError, IndexError):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid date format: {date}. Expected format is YYYY-MM-DD"
                )
        
        # Run the backtest
        results = await run_backtest(
            backtest_request.portfolio_id,
            backtest_request.allocation_dates,
            backtest_request.start_month
        )
        
        # Check if the backtest was successful
        any_errors = any(result.get("status") == "error" for result in results)
        
        if any_errors:
            # Find the first error
            error_month = next((result["month"] for result in results if result.get("status") == "error"), None)
            error_message = next((result["message"] for result in results if result.get("status") == "error"), "Unknown error")
            
            return {
                "status": "partial_success",
                "message": f"Backtest completed with errors up to month {error_month}: {error_message}",
                "results": results
            }
        else:
            return {
                "status": "success",
                "message": f"Successfully completed backtest for {len(results)} months",
                "results": results
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running backtest: {str(e)}"
        ) 