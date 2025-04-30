from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Symbol, Trade
from typing import Optional
import uuid
from datetime import datetime
import pytz
from ..routes.get_stock_price_router import get_stock_price
from .utils import get_symbol_id


async def execute_trade(
    portfolio_id: uuid.UUID,
    symbol: str,
    trade_type: str,
    order_type: str,
    quantity: int,
    reason: str
) -> Optional[Trade]:
    """
    Execute a trade and record it in the trades table.

    Args:
        portfolio_id (uuid.UUID): The ID of the portfolio executing the trade
        symbol (str): The stock symbol to trade
        trade_type (str): Type of trade (e.g., 'BUY', 'SELL')
        order_type (str): Type of order (e.g., 'MARKET', 'LIMIT')
        quantity (int): Number of shares to trade
        reason (str): Reason for the trade

    Returns:
        Optional[Trade]: The created Trade object if successful, None if there's an error
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

            # Get current price for the symbol
            pst = pytz.timezone('America/Los_Angeles')
            current_date = datetime.now(pst).strftime("%Y-%m-%d")
            current_time = datetime.now(pst)
            print(f"Getting price for {symbol} on {current_date}")
            price = await get_stock_price(symbol, current_date)
            print(f"Price for {symbol} on {current_date}: {price}")

            # Update symbol price
            symbol_record = session.query(Symbol).filter(Symbol.symbol_id == symbol_id).first()
            if symbol_record:
                symbol_record.last_updated_at = current_time
                session.commit()

            # Create trade record
            new_trade = Trade(
                trade_id=uuid.uuid4(),
                portfolio_id=portfolio_id,
                symbol_id=symbol_id,
                traded_at=current_time,
                trade_type=trade_type,
                order_type=order_type,
                price=price,
                quantity=quantity,
                reason=reason
            )
            print(f"Trade record: {new_trade}")

            session.add(new_trade)
            session.commit()
            session.refresh(new_trade)
            print(f"Trade executed successfully for {symbol}")
            return new_trade

    except Exception as e:
        print(f"Error executing trade for '{symbol}': {str(e)}")
        return None