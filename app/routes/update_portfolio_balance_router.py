from fastapi import APIRouter, HTTPException
from typing import Optional
from ..service.update_portfolio_balance import update_portfolio_balance
from pydantic import BaseModel

router = APIRouter(
    tags=["Partial Trades"]
)

class PortfolioBalanceUpdate(BaseModel):
    portfolio_id: str
    balance_change: float

@router.put("/update-portfolio-balance", response_model=dict)
def update_balance(update_data: PortfolioBalanceUpdate):
    """
    Update the portfolio balance for a given portfolio_id.

    Args:
        update_data (PortfolioBalanceUpdate): Contains portfolio_id and balance_change

    Returns:
        dict: A dictionary containing the updated portfolio stats

    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        result = update_portfolio_balance(
            update_data.portfolio_id,
            update_data.balance_change
        )
        if result:
            return result
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Portfolio with ID '{update_data.portfolio_id}' not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating portfolio balance: {str(e)}"
        ) 