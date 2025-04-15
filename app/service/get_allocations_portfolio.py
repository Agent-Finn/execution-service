from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..models import Allocation  # Import the Allocation model
from ..database import SessionLocal  # Import SessionLocal for sync ORM
from uuid import UUID
def get_allocations_by_portfolio(portfolio_id: UUID):
    """
    Fetch all allocations for a given portfolio_id.
    
    Args:
        portfolio_id (UUID): The portfolio ID to filter allocations.
    
    Returns:
        dict: A list of allocations in the format {"allocations": [...]}.
    
    Raises:
        HTTPException: 404 if no allocations are found, 500 for other errors.
    """
    try:
        with SessionLocal() as session:
            # Query allocations for the given portfolio_id
            allocations = session.query(Allocation).filter(Allocation.portfolio_id == portfolio_id).all()
            
            if not allocations:
                raise HTTPException(status_code=404, detail=f"No allocations found for portfolio_id {portfolio_id}")
            
            # Convert to dicts for response
            allocations_list = [
                {
                    "allocation_id": alloc.allocation_id,
                    "portfolio_id": alloc.portfolio_id,
                    "allocated_at": alloc.allocated_at.isoformat() if alloc.allocated_at else None,
                    "symbol_id": alloc.symbol_id,
                    "allocation_pct": float(alloc.allocation_pct) if alloc.allocation_pct is not None else None
                }
                for alloc in allocations
            ]
            return {"allocations": allocations_list}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Failed to fetch allocations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch allocations: {str(e)}")