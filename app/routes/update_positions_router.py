from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime
from ..service.update_positions import update_positions, BUY, SELL
from ..models import Position

router = APIRouter(
    tags=["Partial Trades"]
)

class PositionUpdateRequest(BaseModel):
    portfolio_id: uuid.UUID = Field(..., description="The ID of the portfolio")
    symbol: str = Field(..., description="The stock symbol")
    trade_type: str = Field(..., description="Type of trade (e.g., 'Buy', 'Sell')")
    quantity: int = Field(..., gt=0, description="Number of shares to trade")

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "8dc8badc-3418-4f0f-aabd-28a8abff8bcd",
                "symbol": "GOOGL",
                "trade_type": "Buy",
                "quantity": 10
            }
        }

class PositionResponse(BaseModel):
    position_id: uuid.UUID
    portfolio_id: uuid.UUID
    symbol_id: uuid.UUID
    quantity: int
    recorded_at: datetime

    class Config:
        from_attributes = True

@router.post("/update-positions", response_model=PositionResponse)
async def update_positions_endpoint(position_request: PositionUpdateRequest):
    """
    Update positions based on trade execution.
    
    Args:
        position_request (PositionUpdateRequest): The request containing position update details
    
    Returns:
        PositionResponse: The updated position details
    
    Raises:
        HTTPException: If the position update fails
    """
    if position_request.trade_type not in [BUY, SELL]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trade type. Must be either '{BUY}' or '{SELL}'"
        )

    position = update_positions(
        portfolio_id=position_request.portfolio_id,
        quantity=position_request.quantity,
        symbol=position_request.symbol,
        trade_type=position_request.trade_type
    )

    if not position:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update position for {position_request.symbol}"
        )

    return position 