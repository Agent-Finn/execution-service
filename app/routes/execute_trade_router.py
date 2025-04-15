from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime
from ..service.execute_trade import execute_trade
from ..models import Trade

router = APIRouter(
    prefix="/api/v1",
    tags=["Partial Trades"]
)

class TradeRequest(BaseModel):
    portfolio_id: uuid.UUID = Field(..., description="The ID of the portfolio executing the trade")
    symbol: str = Field(..., description="The stock symbol to trade")
    trade_type: str = Field(..., description="Type of trade (e.g., 'BUY', 'SELL')")
    order_type: str = Field(..., description="Type of order (e.g., 'MARKET', 'LIMIT')")
    quantity: int = Field(..., gt=0, description="Number of shares to trade")
    reason: str = Field(..., description="Reason for the trade")

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "5565d9e2-cc13-4629-98ff-214c34cb8fba",
                "symbol": "AAPL",
                "trade_type": "Buy",
                "order_type": "Market",
                "quantity": 10,
                "reason": "Portfolio rebalancing"
            }
        }

class TradeResponse(BaseModel):
    trade_id: uuid.UUID
    portfolio_id: uuid.UUID
    symbol_id: uuid.UUID
    traded_at: datetime
    trade_type: str
    order_type: str
    price: float
    quantity: int
    reason: str

    class Config:
        from_attributes = True

@router.post("/execute-trade", response_model=TradeResponse)
async def execute_trade_endpoint(trade_request: TradeRequest):
    """
    Execute a trade and record it in the trades table.
    
    Args:
        trade_request (TradeRequest): The trade details including portfolio_id, symbol, trade_type, etc.
    
    Returns:
        TradeResponse: The created trade record
    
    Raises:
        HTTPException: If the trade execution fails or if the symbol is not found
    """
    try:
        trade = await execute_trade(
            portfolio_id=trade_request.portfolio_id,
            symbol=trade_request.symbol,
            trade_type=trade_request.trade_type,
            order_type=trade_request.order_type,
            quantity=trade_request.quantity,
            reason=trade_request.reason
        )
        
        if not trade:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol '{trade_request.symbol}' not found in database"
            )
            
        return trade
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing trade: {str(e)}"
        )
