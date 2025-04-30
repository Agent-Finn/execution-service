import asyncio
import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import uuid
from sqlalchemy import text
from decimal import Decimal
from ..database import SessionLocal
from ..models import Position, PortfolioStats, Symbol

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def ensure_initial_position(portfolio_id: str) -> bool:
    """
    Ensure the portfolio has an initial MONEY_MARKET position for the start of the year.
    
    Args:
        portfolio_id: The UUID of the portfolio
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with SessionLocal() as session:
            # Check if we already have positions for this portfolio
            portfolio_uuid = uuid.UUID(portfolio_id)
            
            # Query existing positions
            existing_position = session.execute(
                text("SELECT * FROM positions WHERE portfolio_id = :portfolio_id LIMIT 1"),
                {"portfolio_id": portfolio_uuid}
            ).fetchone()
            
            if existing_position:
                # Delete existing positions
                logger.info(f"Clearing existing positions for portfolio {portfolio_id}")
                session.execute(
                    text("DELETE FROM positions WHERE portfolio_id = :portfolio_id"),
                    {"portfolio_id": portfolio_uuid}
                )
            
            # Clear existing portfolio stats
            logger.info(f"Clearing existing portfolio stats for portfolio {portfolio_id}")
            session.execute(
                text("DELETE FROM portfolio_stats WHERE portfolio_id = :portfolio_id"),
                {"portfolio_id": portfolio_uuid}
            )
            
            # Clear existing trades
            logger.info(f"Clearing existing trades for portfolio {portfolio_id}")
            session.execute(
                text("DELETE FROM trades WHERE portfolio_id = :portfolio_id"),
                {"portfolio_id": portfolio_uuid}
            )
            
            # Get the MONEY_MARKET symbol_id
            money_market_symbol = session.query(Symbol).filter(Symbol.symbol == "MONEY_MARKET").first()
            
            if not money_market_symbol:
                # If MONEY_MARKET symbol doesn't exist, use a hardcoded ID
                logger.warning("MONEY_MARKET symbol not found, using hardcoded ID")
                money_market_id = uuid.UUID("3741a1c6-f87b-44e2-a10a-b62a1b372a82")
            else:
                money_market_id = money_market_symbol.symbol_id
            
            # Create a position for January 1st, 2024
            jan_first = date(2024, 1, 1)
            position_id = uuid.uuid4()
            
            # Add position record
            new_position = Position(
                position_id=position_id,
                portfolio_id=portfolio_uuid,
                symbol_id=money_market_id,
                quantity=1000000,  # Start with $1,000,000
                recorded_at=datetime.combine(jan_first, datetime.min.time())
            )
            session.add(new_position)
            
            # Add initial portfolio stats
            new_stats = PortfolioStats(
                stat_id=uuid.uuid4(),
                portfolio_id=portfolio_uuid,
                portfolio_balance=Decimal('1000000'),
                recorded_at=datetime.combine(jan_first, datetime.min.time()),
                alpha=Decimal('0'),
                beta=Decimal('0'),
                max_drawdown=Decimal('0'),
                sharpe_ratio=Decimal('0'),
                std_dev=Decimal('0'),
                turnover=Decimal('0')
            )
            session.add(new_stats)
            
            # Commit the changes
            session.commit()
            logger.info(f"Initial position and portfolio stats created for portfolio {portfolio_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error ensuring initial position for portfolio {portfolio_id}: {str(e)}")
        return False

async def get_allocation_batch_id_for_date(allocation_date: str) -> Optional[str]:
    """
    Get the allocation_batch_id for a specific allocation date from the database.
    
    Args:
        allocation_date: Date in format YYYY-MM-DD
    
    Returns:
        allocation_batch_id if found, None otherwise
    """
    try:
        # Use SessionLocal directly to create a database session
        with SessionLocal() as db:
            # Query to get the allocation_batch_id for the given date
            query = text("""
                SELECT allocation_batch_id 
                FROM allocations 
                WHERE allocated_at::date = :allocation_date 
                LIMIT 1
            """)
            result = db.execute(query, {"allocation_date": allocation_date}).fetchone()
            
            if result:
                return str(result[0])
            else:
                logger.error(f"No allocation batch found for date: {allocation_date}")
                return None
    except Exception as e:
        logger.error(f"Error retrieving allocation batch for date {allocation_date}: {str(e)}")
        return None

async def update_portfolio_balance_for_month(portfolio_id: str, year: int, month: int) -> Dict[str, Any]:
    """
    Call the update-portfolio-balance endpoint for a specific month.
    
    Args:
        portfolio_id: The UUID of the portfolio
        year: The year (e.g., 2024)
        month: The month (1-12)
    
    Returns:
        The response from the update-portfolio-balance endpoint
    """
    logger.info(f"Updating portfolio balance for {year}-{month:02d}")
    
    async with httpx.AsyncClient() as client:
        payload = {
            "portfolio_id": portfolio_id,
            "year": year,
            "month": month
        }
        
        try:
            response = await client.post(
                "http://localhost:8080/update-portfolio-balance",
                json=payload,
                timeout=300  # Long timeout for potentially lengthy operations
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated portfolio balance for {year}-{month:02d}")
            return result
        except Exception as e:
            logger.error(f"Error updating portfolio balance for {year}-{month:02d}: {str(e)}")
            return {"status": "error", "message": str(e)}

async def plan_full_trade(allocation_batch_id: str) -> Dict[str, Any]:
    """
    Call the plan-full-trade endpoint with a specific allocation_batch_id.
    
    Args:
        allocation_batch_id: The UUID of the allocation batch
    
    Returns:
        The response from the plan-full-trade endpoint
    """
    logger.info(f"Planning full trade for allocation batch ID: {allocation_batch_id}")
    
    async with httpx.AsyncClient() as client:
        payload = {
            "allocation_batch_id": allocation_batch_id
        }
        
        try:
            response = await client.post(
                "http://localhost:8080/plan-full-trade",
                json=payload,
                timeout=300  # Long timeout for potentially lengthy operations
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully planned full trade for allocation batch ID: {allocation_batch_id}")
            return result
        except Exception as e:
            logger.error(f"Error planning full trade for allocation batch ID {allocation_batch_id}: {str(e)}")
            return {"status": "error", "message": str(e)}

async def run_backtest(portfolio_id: str, allocation_dates: List[str], start_month: int = 1) -> List[Dict[str, Any]]:
    """
    Run a backtest for a portfolio, sequentially updating the portfolio balance and planning trades for each month.
    
    Args:
        portfolio_id: The UUID of the portfolio
        allocation_dates: List of allocation dates in YYYY-MM-DD format
        start_month: The month to start from (default is January=1)
    
    Returns:
        List of results for each month's operations
    """
    results = []
    year = 2024  # Hardcoded for now, could be made dynamic
    
    # Step 0: Ensure we have an initial position for January 1st
    init_success = await ensure_initial_position(portfolio_id)
    if not init_success:
        return [{
            "month": 0,
            "update_result": None,
            "trade_result": None,
            "status": "error",
            "message": "Failed to initialize positions for portfolio"
        }]
    
    # Filter allocation dates to only include those from start_month onwards
    filtered_dates = [date for date in allocation_dates 
                     if int(date.split('-')[1]) >= start_month]
    
    for allocation_date in filtered_dates:
        month = int(allocation_date.split('-')[1])
        
        # Step 1: Update portfolio balance for the month
        update_result = await update_portfolio_balance_for_month(portfolio_id, year, month)
        
        if update_result.get("status") == "error":
            results.append({
                "month": month,
                "update_result": update_result,
                "trade_result": None,
                "status": "error",
                "message": f"Failed to update portfolio balance for month {month}"
            })
            logger.error(f"Stopping backtest due to error in month {month}")
            break
        
        # Step 2: Get allocation_batch_id for the month
        allocation_batch_id = await get_allocation_batch_id_for_date(allocation_date)
        
        if not allocation_batch_id:
            results.append({
                "month": month,
                "update_result": update_result,
                "trade_result": None,
                "status": "error",
                "message": f"No allocation batch found for date {allocation_date}"
            })
            logger.error(f"Stopping backtest due to missing allocation batch for {allocation_date}")
            break
        
        # Step 3: Plan full trade using the allocation_batch_id
        trade_result = await plan_full_trade(allocation_batch_id)
        
        if trade_result.get("status") == "error":
            results.append({
                "month": month,
                "update_result": update_result,
                "trade_result": trade_result,
                "status": "error",
                "message": f"Failed to plan trade for month {month}"
            })
            logger.error(f"Stopping backtest due to error in planning trade for month {month}")
            break
        
        # Successfully processed this month
        results.append({
            "month": month,
            "update_result": update_result,
            "trade_result": trade_result,
            "status": "success",
            "message": f"Successfully processed month {month}"
        })
        
        logger.info(f"Completed processing for month {month}")
        
    return results 