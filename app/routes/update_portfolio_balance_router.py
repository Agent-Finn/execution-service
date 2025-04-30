from fastapi import APIRouter, HTTPException
from typing import Optional
from ..service.update_portfolio_balance import update_portfolio_balance
from pydantic import BaseModel, Field

router = APIRouter(
    tags=["Portfolio Management"]
)

class PortfolioBalanceUpdateRequest(BaseModel):
    portfolio_id: str = Field(..., description="UUID of the portfolio")
    year: int = Field(..., description="Year of the month to update (e.g. 2024)")
    month: int = Field(..., ge=1, le=12, description="Month to update (1-12)")

@router.post("/update-portfolio-balance", response_model=dict)
def update_balance(update_data: PortfolioBalanceUpdateRequest):
    """
    Update portfolio balances for all trading days in a given month.
    
    For each trading day in the month:
    - Gets the positions for that month
    - Looks up prices for each position on that trading day
    - Calculates the total portfolio value
    - Saves the portfolio stats with the calculated balance
    
    Args:
        update_data (PortfolioBalanceUpdateRequest): Contains portfolio_id, year, and month

    Returns:
        dict: A dictionary containing the results of the update operation

    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        result = update_portfolio_balance(
            update_data.portfolio_id,
            update_data.year,
            update_data.month
        )
        if result and result.get("status") == "success":
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating portfolio balance: {result.get('message')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating portfolio balance: {str(e)}"
        ) 