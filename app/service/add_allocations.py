import uuid
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..database import SessionLocal
from ..models import Allocation, Symbol
from .utils import get_symbol_id

async def add_allocations(portfolio_id: str, date: str, allocations: Dict[str, float]) -> str:
    """
    Add allocations for a portfolio.
    
    Args:
        portfolio_id (str): The portfolio ID to create allocations for
        date (str): The date for allocations in format 'YYYY-MM-DD'
        allocations (Dict[str, float]): Dictionary of ticker:allocation_pct pairs
        
    Returns:
        str: The allocation_batch_id if successful
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Validate that allocation percentages add up to 1
        total_allocation = sum(allocations.values())
        if abs(total_allocation - 1.0) > 0.0001:  # Allow for minor floating point precision issues
            raise ValueError(f"Allocation percentages must add up to 1. Current total: {total_allocation}")
        
        # Create a new UUID for the allocation batch
        allocation_batch_id = uuid.uuid4()
        
        # Convert date string to datetime
        allocated_at = datetime.strptime(date, "%Y-%m-%d")
        
        # Convert portfolio_id string to UUID
        portfolio_uuid = uuid.UUID(portfolio_id)
        
        successful_allocations = []
        
        with SessionLocal() as session:
            # Process each ticker and its allocation
            for ticker, allocation_pct in allocations.items():
                # Get symbol_id for the ticker
                symbol_id = get_symbol_id(session, ticker)
                
                if not symbol_id:
                    raise ValueError(f"Symbol {ticker} not found in database")
                
                # Create a new allocation
                new_allocation = Allocation(
                    allocation_id=uuid.uuid4(),
                    portfolio_id=portfolio_uuid,
                    symbol_id=symbol_id,
                    allocation_pct=Decimal(allocation_pct),
                    allocated_at=allocated_at,
                    allocation_batch_id=allocation_batch_id
                )
                
                session.add(new_allocation)
                successful_allocations.append(new_allocation)
            
            # Commit all allocations to the database
            session.commit()
            
            return str(allocation_batch_id)
    
    except Exception as e:
        # Rollback in case of error
        if 'session' in locals():
            session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create allocations: {str(e)}") 