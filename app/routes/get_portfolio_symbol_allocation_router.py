from fastapi import APIRouter
from typing import Dict
from uuid import UUID
from ..service.get_portfolio_symbol_allocation import get_portfolio_symbol_allocation

router = APIRouter(
    prefix="/api/v1",
    tags=["Portfolio Analysis"]
)

@router.get("/portfolio/{portfolio_id}/symbol-allocation", response_model=Dict)
async def get_symbol_allocation(portfolio_id: UUID):
    """
    Get the allocation percentages for each symbol in a portfolio based on quantity.
    
    Args:
        portfolio_id (UUID): The ID of the portfolio to analyze
        
    Returns:
        Dict: A dictionary containing portfolio_id, allocations mapping symbols to percentages,
              and total quantity
    """
    return get_portfolio_symbol_allocation(portfolio_id) 