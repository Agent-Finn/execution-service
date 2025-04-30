from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from ..service.random_allocations import generate_random_allocations, generate_monthly_random_allocations

# Define request model for single date
class RandomAllocationCreate(BaseModel):
    portfolio_id: str
    date: str = Field(..., description="Allocation date in format 'YYYY-MM-DD'")

# Define request model for monthly allocations
class MonthlyRandomAllocationCreate(BaseModel):
    portfolio_id: str
    year: int = Field(..., description="Year to generate allocations for", gt=2000, lt=2100)

# Define response models
class RandomAllocationResponse(BaseModel):
    allocation_date: str
    allocation_batch_id: str
    allocations: List[Dict[str, Any]]

class MonthlyRandomAllocationResponse(BaseModel):
    allocation_batches: List[Dict[str, Any]]

# Create router
router = APIRouter(
    prefix="/allocations",
    tags=["Allocations"]
)

@router.post("/random", response_model=RandomAllocationResponse)
async def create_random_allocations(allocation_data: RandomAllocationCreate):
    """
    Generate random allocations for a portfolio for a specific date.
    
    This endpoint will:
    - Select 10-20 random symbols from the database
    - Generate random allocation percentages that sum to 1
    - Create a new allocation batch with these allocations
    
    Args:
        allocation_data (RandomAllocationCreate): Contains portfolio_id and date
        
    Returns:
        RandomAllocationResponse: The allocation batch details
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        allocation_batch = await generate_random_allocations(
            allocation_data.portfolio_id,
            allocation_data.date
        )
        
        return allocation_batch
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating random allocations: {str(e)}"
        )

@router.post("/random-monthly", response_model=MonthlyRandomAllocationResponse)
async def create_monthly_random_allocations(allocation_data: MonthlyRandomAllocationCreate):
    """
    Generate random allocations for a portfolio for each month in the specified year.
    
    This endpoint will, for each month:
    - Select 10-20 random symbols from the database
    - Generate random allocation percentages that sum to 1
    - Create a new allocation batch with these allocations
    - Use the last day of each month as the allocation date
    
    Args:
        allocation_data (MonthlyRandomAllocationCreate): Contains portfolio_id and year
        
    Returns:
        MonthlyRandomAllocationResponse: A list of allocation batches, one for each month
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        allocation_batches = await generate_monthly_random_allocations(
            allocation_data.portfolio_id,
            allocation_data.year
        )
        
        return {
            "allocation_batches": allocation_batches
        }
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating monthly random allocations: {str(e)}"
        ) 