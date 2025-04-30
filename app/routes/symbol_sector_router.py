from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Optional
from uuid import UUID
from ..service.add_symbol_sector import add_symbol_sector

router = APIRouter(
    prefix="/symbol-sectors",
    tags=["symbol_sectors"]
)

class SymbolSectorCreate(BaseModel):
    symbol: str
    sector: str
    pct: float
    
    @validator('pct')
    def validate_percentage(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Percentage must be between 0 and 1')
        return v

@router.post("/", response_model=dict)
async def create_symbol_sector(data: SymbolSectorCreate):
    """
    Add a symbol-sector relationship to the symbol_sectors table.
    The sum of all percentages for a symbol must equal exactly 1.
    
    Args:
        data: The SymbolSectorCreate object containing symbol, sector, and pct
        
    Returns:
        dict: Details of the created or updated record
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        result = add_symbol_sector(data.symbol, data.sector, data.pct)
        if result:
            return result
        else:
            raise HTTPException(
                status_code=400,
                detail="Symbol or sector not found, or the total percentage allocation for this symbol would not equal 1"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error adding symbol-sector relationship: {str(e)}"
        ) 