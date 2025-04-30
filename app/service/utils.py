from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models import Symbol, SymbolPrice
from typing import Optional
import uuid
from datetime import datetime, date, timedelta, time, timezone


def get_symbol_id(session: Session, symbol: str) -> Optional[uuid.UUID]:
    """
    Look up the symbol_id for a given symbol.

    Args:
        session (Session): SQLAlchemy session
        symbol (str): The stock symbol to look up

    Returns:
        Optional[uuid.UUID]: The symbol_id if found, None otherwise
    """
    symbol_record = session.query(Symbol).filter(Symbol.symbol == symbol).first()
    return symbol_record.symbol_id if symbol_record else None

def get_symbol_price(session: Session, symbol_id: uuid.UUID, price_date: date) -> float:
    """
    Get the price of a symbol for a specific date from the symbol_prices table.
    
    Args:
        session (Session): The database session
        symbol_id (uuid.UUID): The symbol ID
        price_date (date): The date for price lookup
        
    Returns:
        float: The price of the symbol
    """
    # Check if this is the MONEY_MARKET symbol
    symbol_name = get_symbol_name(session, symbol_id)
    if symbol_name == "MONEY_MARKET":
        return 1.00  # Always return 1.00 for MONEY_MARKET

    # Query the price from symbol_prices for this symbol on the given date
    symbol_price = session.query(SymbolPrice).filter(
        SymbolPrice.symbol_id == symbol_id,
        SymbolPrice.price_at == price_date
    ).first()
    
    if symbol_price:
        return float(symbol_price.price)
    else:
        # If no price found for the exact date, log a warning
        print(f"WARNING: No price found for symbol {symbol_name} ({symbol_id}) on {price_date}")
        
        # Try to find the most recent price before this date
        most_recent_price = session.query(SymbolPrice).filter(
            SymbolPrice.symbol_id == symbol_id,
            SymbolPrice.price_at < price_date
        ).order_by(desc(SymbolPrice.price_at)).first()
        
        if most_recent_price:
            print(f"Using most recent price from {most_recent_price.price_at} for {symbol_name}: ${float(most_recent_price.price):.2f}")
            return float(most_recent_price.price)
        else:
            print(f"ERROR: No price data available for {symbol_name} ({symbol_id})")
            return 0

def get_symbol_name(session: Session, symbol_id: uuid.UUID) -> str:
    symbol_record = session.query(Symbol).filter(Symbol.symbol_id == symbol_id).first()
    return symbol_record.symbol if symbol_record else f"Unknown ({symbol_id})"

