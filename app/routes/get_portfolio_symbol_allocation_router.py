from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from pydantic import BaseModel
from ..database import SessionLocal
from ..service.get_portfolio_symbol_allocation import calculate_sector_allocations

router = APIRouter(
    prefix="/sector-allocations",
    tags=["sector_allocations"],
)

class SectorAllocation(BaseModel):
    sector_id: str
    sector_pct: float

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{batch_id}", response_model=List[SectorAllocation])
def get_sector_allocations(batch_id: UUID, db: Session = Depends(get_db)):
    """
    Calculate and return sector allocations for a given batch ID.
    
    Args:
        batch_id (UUID): The ID of the allocation batch.
        db (Session): The database session, provided via dependency.
    
    Returns:
        List[SectorAllocation]: A list of sector allocations.
    
    Raises:
        HTTPException: If no allocations are found for the batch.
    """
    result = calculate_sector_allocations(db, batch_id)
    if not result:
        raise HTTPException(status_code=404, detail="No allocations found for this batch")
    return result