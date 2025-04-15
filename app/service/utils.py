from sqlalchemy.orm import Session
from ..models import Symbol
from typing import Optional
import uuid

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
