from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from ..service.execute_full_trade import execute_full_trade

router = APIRouter(
    tags=["Trade Execution"]
)

class FullTradeRequest(BaseModel):
    allocation_batch_id: uuid.UUID = Field(..., description="The batch ID for the allocations to use")

    class Config:
        json_schema_extra = {
            "example": {
                "allocation_batch_id": "8dc8badc-3418-4f0f-aabd-28a8abff8bcd"
            }
        }

class TradeResponse(BaseModel):
    trade_id: str
    portfolio_id: str
    symbol_id: str
    symbol: str
    trade_type: str
    quantity: int
    price: float
    total_value: float

class FullTradeResponse(BaseModel):
    status: str
    message: str
    portfolio_id: Optional[str] = None
    allocation_batch_id: Optional[str] = None
    portfolio_balance: Optional[float] = None
    planned_trades: Optional[List[TradeResponse]] = None

@router.post("/plan-full-trade", response_model=FullTradeResponse)
async def plan_full_trade_endpoint(trade_request: FullTradeRequest):
    """
    Plan a full trade based on allocation batch and current positions, without executing it.
    
    This endpoint:
    1. Gets existing portfolio balance from the portfolio_stats table
    2. Gets allocations from the specified batch_id
    3. Gets stock prices for the timestamp in the allocation batch
    4. Calculates what to buy and sell based on allocations and current positions
    5. Returns the planned trades without executing them
    
    Args:
        trade_request (FullTradeRequest): Contains allocation_batch_id
    
    Returns:
        FullTradeResponse: Results of the trade planning
    
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        result = await execute_full_trade(
            trade_request.allocation_batch_id
        )
        
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
            detail=f"Error planning full trade: {str(e)}"
        ) 