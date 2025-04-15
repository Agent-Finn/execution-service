from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Position, Symbol
from typing import Optional
import uuid
from datetime import datetime
import pytz
from .utils import get_symbol_id

BUY = "Buy"
SELL = "Sell"


def update_positions(portfolio_id: uuid.UUID, quantity: int, symbol: str, trade_type: str) -> Optional[Position]:
    """
    Update positions table based on trade execution.

    Args:
        portfolio_id (uuid.UUID): The ID of the portfolio
        quantity (int): Number of shares to trade
        symbol (str): The stock symbol
        trade_type (str): Type of trade (e.g., 'BUY', 'SELL')

    Returns:
        Optional[Position]: The updated Position object if successful, None if there's an error
    """
    try:
        with SessionLocal() as session:
            # Clear the session cache to ensure we have the latest database state
            session.expire_all()
            
            # Look up symbol_id
            symbol_id = get_symbol_id(session, symbol)
            if not symbol_id:
                print(f"Symbol '{symbol}' not found in database")
                return None

            # Get current time in PST
            pst = pytz.timezone('America/Los_Angeles')
            current_time = datetime.now(pst)

            # Find existing position
            position = session.query(Position).filter(
                Position.portfolio_id == portfolio_id,
                Position.symbol_id == symbol_id
            ).first()

            if position:
                # Update existing position
                if trade_type == BUY:
                    position.quantity += quantity
                elif trade_type == SELL:
                    position.quantity -= quantity
                position.recorded_at = current_time
            else:
                # Create new position if it doesn't exist
                if trade_type == BUY:
                    position = Position(
                        position_id=uuid.uuid4(),
                        portfolio_id=portfolio_id,
                        symbol_id=symbol_id,
                        quantity=quantity,
                        recorded_at=current_time
                    )
                    session.add(position)
                else:
                    print(f"Cannot sell {quantity} shares of {symbol} - no existing position")
                    return None

            session.commit()
            session.refresh(position)
            print(f"Position updated successfully for {symbol}")
            return position

    except Exception as e:
        print(f"Error updating position for '{symbol}': {str(e)}")
        return None

