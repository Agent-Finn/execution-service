from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from ..service.add_allocations import add_allocations

# Define request model
class AllocationCreate(BaseModel):
    portfolio_id: str
    date: str = Field(..., description="Allocation date in format 'YYYY-MM-DD'")
    allocations: Dict[str, float] = Field(..., description="Dictionary of ticker:allocation_pct pairs")

# Create router
router = APIRouter(
    prefix="/allocations",
    tags=["Allocations"]
)

@router.post("/", response_model=dict)
async def create_allocations(allocation_data: AllocationCreate):
    """
    Add allocations for a portfolio.
    
    The sum of all allocation percentages must equal 1.
    Each ticker symbol will be matched to its corresponding symbol_id.
    All allocations will share the same allocation_batch_id.
    
    Args:
        allocation_data (AllocationCreate): Contains portfolio_id, date, and allocations
        
    Returns:
        dict: The allocation_batch_id if successful
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        allocation_batch_id = await add_allocations(
            allocation_data.portfolio_id,
            allocation_data.date,
            allocation_data.allocations
        )
        
        return {"allocation_batch_id": allocation_batch_id}
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating allocations: {str(e)}"
        ) 