from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import SessionLocal
from ..models import Position, Symbol
from typing import Optional
import uuid
from datetime import datetime
import pytz
from .utils import get_symbol_id
from decimal import Decimal

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
        Optional[Position]: The new Position object if successful, None if there's an error
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

            # Find the most recent existing position for this symbol
            existing_position = session.query(Position).filter(
                Position.portfolio_id == portfolio_id,
                Position.symbol_id == symbol_id
            ).order_by(desc(Position.recorded_at)).first()

            # Calculate new quantity
            new_quantity = quantity
            if existing_position:
                if trade_type == BUY:
                    new_quantity = existing_position.quantity + quantity
                elif trade_type == SELL:
                    if existing_position.quantity < quantity:
                        print(f"Cannot sell {quantity} shares of {symbol} - only have {existing_position.quantity}")
                        return None
                    new_quantity = existing_position.quantity - quantity
            elif trade_type == SELL:
                print(f"Cannot sell {quantity} shares of {symbol} - no existing position")
                return None

            # Create a new position record with the updated quantity
            new_position = Position(
                position_id=uuid.uuid4(),
                portfolio_id=portfolio_id,
                symbol_id=symbol_id,
                quantity=new_quantity,
                recorded_at=current_time
            )
            
            session.add(new_position)
            session.commit()
            session.refresh(new_position)
            print(f"Position updated successfully for {symbol}")
            return new_position

    except Exception as e:
        print(f"Error updating position for '{symbol}': {str(e)}")
        return None

