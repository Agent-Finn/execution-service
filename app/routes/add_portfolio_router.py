from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..service.add_portfolio import add_portfolio

# Define request model
class PortfolioCreate(BaseModel):
    user_id: str
    portfolio_name: str
    date: str = None  # Optional date parameter (format: YYYY-MM-DD)

# Create router
router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"]
)

@router.post("/", response_model=dict)
async def create_portfolio(portfolio: PortfolioCreate):
    """
    Add a new portfolio for a user.

    Args:
        portfolio (PortfolioCreate): The portfolio details including user_id and portfolio_name

    Returns:
        dict: A dictionary containing the portfolio details if added successfully

    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        result = await add_portfolio(portfolio.user_id, portfolio.portfolio_name, portfolio.date)
        if result:
            return {
                "portfolio_id": str(result.portfolio_id),
                "user_id": str(result.user_id),
                "portfolio_name": result.portfolio_name,
                "last_updated_at": result.last_updated_at
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create portfolio '{portfolio.portfolio_name}' for user {portfolio.user_id}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error adding portfolio: {str(e)}"
        ) 