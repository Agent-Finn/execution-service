import uuid
import random
import calendar
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..database import SessionLocal
from ..models import Allocation, Symbol
from sqlalchemy import func

def is_weekday(day: date) -> bool:
    """
    Check if a date is a weekday (Monday to Friday).
    
    Args:
        day (date): The date to check
        
    Returns:
        bool: True if the date is a weekday, False otherwise
    """
    # 0 is Monday, 6 is Sunday in the Python date.weekday() system
    return day.weekday() < 5  # Weekdays are 0-4 (Monday to Friday)

def get_first_trading_days_of_months(year: int) -> List[date]:
    """
    Get the first trading day (weekday) of each month for a given year.
    
    Args:
        year (int): The year to get first trading days for
        
    Returns:
        List[date]: List of dates representing the first trading day of each month
    """
    first_trading_days = []
    for month in range(1, 13):
        # Start with the first day of the month
        current_day = date(year, month, 1)
        
        # If it's not a weekday, find the next weekday
        while not is_weekday(current_day):
            current_day += timedelta(days=1)
            
        first_trading_days.append(current_day)
    return first_trading_days

async def generate_random_allocations(portfolio_id: str, date_str: str) -> Dict:
    """
    Generate random allocations for a portfolio for a specific date.
    
    Args:
        portfolio_id (str): The portfolio ID to create allocations for
        date_str (str): The date for allocations in format 'YYYY-MM-DD'
        
    Returns:
        Dict: The allocation batch result
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Parse the date string
        allocation_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Convert portfolio_id string to UUID
        portfolio_uuid = uuid.UUID(portfolio_id)
        
        with SessionLocal() as session:
            # Get a list of all symbols
            all_symbols = session.query(Symbol.symbol_id, Symbol.symbol).all()
            
            if not all_symbols:
                raise ValueError("No symbols found in database")
            
            # Create a new UUID for this allocation batch
            allocation_batch_id = uuid.uuid4()
            
            # Convert date to datetime for storage
            allocated_at = datetime.combine(allocation_date, datetime.min.time())
            
            # Randomly select 10-20 symbols
            num_symbols = 5#= random.randint(10, 20)
            
            # Make sure we don't select more symbols than are available
            num_symbols = min(num_symbols, len(all_symbols))
            
            selected_symbols = random.sample(all_symbols, num_symbols)
            
            # Generate random weights
            random_weights = [random.random() for _ in range(num_symbols)]
            
            # Normalize weights to sum to 1
            total_weight = sum(random_weights)
            normalized_weights = [weight / total_weight for weight in random_weights]
            
            batch_allocations = []
            
            # Create allocations
            for i, (symbol_id, symbol) in enumerate(selected_symbols):
                # Round allocation percentage to 2 decimal places
                allocation_pct = round(normalized_weights[i], 2)
                
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
                
                # Add to results for response
                batch_allocations.append({
                    "allocation_id": str(new_allocation.allocation_id),
                    "symbol_id": str(symbol_id),
                    "symbol": symbol,
                    "allocation_pct": allocation_pct
                })
            
            # After rounding, re-normalize to ensure sum is exactly 1.0
            total_rounded = sum(result["allocation_pct"] for result in batch_allocations)
            if total_rounded != 1.0 and len(batch_allocations) > 0:
                # Add any rounding difference to the largest allocation
                largest_allocation = max(batch_allocations, key=lambda x: x["allocation_pct"])
                adjustment = 1.0 - total_rounded
                
                # Update the largest allocation in both places
                largest_idx = batch_allocations.index(largest_allocation)
                batch_allocations[largest_idx]["allocation_pct"] = round(largest_allocation["allocation_pct"] + adjustment, 2)
                
                # Also update the corresponding Allocation object in the session
                for obj in session.new:
                    if isinstance(obj, Allocation) and str(obj.allocation_id) == largest_allocation["allocation_id"]:
                        obj.allocation_pct = Decimal(batch_allocations[largest_idx]["allocation_pct"])
            
            # Commit all allocations to the database
            session.commit()
            
            return {
                "allocation_date": allocation_date.strftime("%Y-%m-%d"),
                "allocation_batch_id": str(allocation_batch_id),
                "allocations": batch_allocations
            }
    
    except Exception as e:
        # Rollback in case of error
        if 'session' in locals():
            session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create random allocations: {str(e)}")

async def generate_monthly_random_allocations(portfolio_id: str, year: int) -> List[Dict]:
    """
    Generate random allocations for a portfolio for the first trading day of each month of the year.
    
    Args:
        portfolio_id (str): The portfolio ID to create allocations for
        year (int): The year to generate allocations for
        
    Returns:
        List[Dict]: List of allocation batch results for each month
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Get the first trading day of each month in the given year
        first_trading_days = get_first_trading_days_of_months(year)
        
        # Convert portfolio_id string to UUID
        portfolio_uuid = uuid.UUID(portfolio_id)
        
        all_batches = []
        
        with SessionLocal() as session:
            # Get a list of all symbols
            all_symbols = session.query(Symbol.symbol_id, Symbol.symbol).all()
            
            if not all_symbols:
                raise ValueError("No symbols found in database")
            
            # Process each month
            for allocation_date in first_trading_days:
                # Create a new UUID for this allocation batch
                allocation_batch_id = uuid.uuid4()
                
                # Convert date to datetime for storage
                allocated_at = datetime.combine(allocation_date, datetime.min.time())
                
                # Randomly select 10-20 symbols
                num_symbols  = 5 #= random.randint(10, 20)
                
                # Make sure we don't select more symbols than are available
                num_symbols = min(num_symbols, len(all_symbols))
                
                selected_symbols = random.sample(all_symbols, num_symbols)
                
                # Generate random weights
                random_weights = [random.random() for _ in range(num_symbols)]
                
                # Normalize weights to sum to 1
                total_weight = sum(random_weights)
                normalized_weights = [weight / total_weight for weight in random_weights]
                
                batch_allocations = []
                
                # Create allocations for this month
                for i, (symbol_id, symbol) in enumerate(selected_symbols):
                    # Round allocation percentage to 2 decimal places
                    allocation_pct = round(normalized_weights[i], 2)
                    
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
                    
                    # Add to results for response
                    batch_allocations.append({
                        "allocation_id": str(new_allocation.allocation_id),
                        "symbol_id": str(symbol_id),
                        "symbol": symbol,
                        "allocation_pct": allocation_pct
                    })
                
                # After rounding, re-normalize to ensure sum is exactly 1.0
                total_rounded = sum(result["allocation_pct"] for result in batch_allocations)
                if total_rounded != 1.0 and len(batch_allocations) > 0:
                    # Add any rounding difference to the largest allocation
                    largest_allocation = max(batch_allocations, key=lambda x: x["allocation_pct"])
                    adjustment = 1.0 - total_rounded
                    
                    # Update the largest allocation in both places
                    largest_idx = batch_allocations.index(largest_allocation)
                    batch_allocations[largest_idx]["allocation_pct"] = round(largest_allocation["allocation_pct"] + adjustment, 2)
                    
                    # Also update the corresponding Allocation object in the session
                    for obj in session.new:
                        if isinstance(obj, Allocation) and str(obj.allocation_id) == largest_allocation["allocation_id"]:
                            obj.allocation_pct = Decimal(batch_allocations[largest_idx]["allocation_pct"])
                
                # Add this month's batch to the result
                all_batches.append({
                    "allocation_date": allocation_date.strftime("%Y-%m-%d"),
                    "allocation_batch_id": str(allocation_batch_id),
                    "allocations": batch_allocations
                })
            
            # Commit all allocations to the database
            session.commit()
            
            return all_batches
    
    except Exception as e:
        # Rollback in case of error
        if 'session' in locals():
            session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create random allocations: {str(e)}") 