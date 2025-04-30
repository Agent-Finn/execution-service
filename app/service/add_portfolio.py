from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Portfolio, Position, PortfolioStats, Symbol
from typing import Optional
import uuid
from datetime import datetime
import pytz
from decimal import Decimal

async def add_portfolio(user_id: str, portfolio_name: str, date: str = None) -> Optional[Portfolio]:
    """
    Add a portfolio to the portfolios table.

    Args:
        user_id (str): The UUID of the user who owns the portfolio.
        portfolio_name (str): The name of the portfolio.
        date (str, optional): The date for the portfolio in format 'YYYY-MM-DD'. Defaults to current date.

    Returns:
        Optional[Portfolio]: The newly created Portfolio object if added, None on error.
    """
    try:
        with SessionLocal() as session:
            # Clear the session cache to ensure we have the latest database state
            session.expire_all()
            
            # Create a new portfolio with a generated UUID
            pst = pytz.timezone('America/Los_Angeles')
            current_time = datetime.now(pst)
            
            # Parse the date if provided, otherwise use current date
            if date:
                recorded_at = datetime.strptime(date, "%Y-%m-%d")
            else:
                recorded_at = current_time
            
            # Convert user_id string to UUID
            user_uuid = uuid.UUID(user_id)
            
            # Create a new portfolio_id
            portfolio_id = uuid.uuid4()
            
            # Create the new portfolio
            new_portfolio = Portfolio(
                portfolio_id=portfolio_id,
                user_id=user_uuid,
                portfolio_name=portfolio_name,
                last_updated_at=current_time
            )
            
            session.add(new_portfolio)
            
            # Get the MONEY_MARKET symbol_id
            money_market_symbol = session.query(Symbol).filter(Symbol.symbol == "MONEY_MARKET").first()
            
            if not money_market_symbol:
                # If MONEY_MARKET symbol doesn't exist, use the hardcoded ID from the example
                money_market_id = uuid.UUID("3741a1c6-f87b-44e2-a10a-b62a1b372a82")
            else:
                money_market_id = money_market_symbol.symbol_id
            
            # Create a new position with 1,000,000 units of MONEY_MARKET
            new_position = Position(
                position_id=uuid.uuid4(),
                portfolio_id=portfolio_id,
                symbol_id=money_market_id,
                quantity=1000000,
                recorded_at=recorded_at
            )
            
            session.add(new_position)
            
            # Create initial portfolio stats
            new_stats = PortfolioStats(
                stat_id=uuid.uuid4(),
                portfolio_id=portfolio_id,
                portfolio_balance=Decimal('1000000'),
                recorded_at=recorded_at,
                alpha=Decimal('0'),
                beta=Decimal('0'),
                max_drawdown=Decimal('0'),
                sharpe_ratio=Decimal('0'),
                std_dev=Decimal('0'),
                turnover=Decimal('0')
            )
            
            session.add(new_stats)
            
            # Commit all changes to the database
            session.commit()
            
            # Refresh the object to ensure all attributes are loaded
            session.refresh(new_portfolio)
            
            print(f"Portfolio '{portfolio_name}' added successfully for user {user_id} with 1,000,000 units of MONEY_MARKET.")
            return new_portfolio
    except Exception as e:
        print(f"Error adding portfolio '{portfolio_name}' for user {user_id}: {str(e)}")
        return None 