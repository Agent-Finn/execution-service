from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Symbol
from typing import Optional
import uuid
from datetime import datetime
import pytz

async def add_symbol(symbol: str) -> Optional[Symbol]:
    """
    Add a symbol to the symbols table if it doesn't already exist.

    Args:
        symbol (str): The symbol to add.

    Returns:
        Optional[Symbol]: The newly created Symbol object if added, None if it already exists or on error.
    """
    try:
        with SessionLocal() as session:
            # Clear the session cache to ensure we have the latest database state
            session.expire_all()
            
            # Check if the symbol already exists
            existing_symbol = session.query(Symbol).filter(Symbol.symbol == symbol).first()
            if existing_symbol:
                print(f"Symbol '{symbol}' already exists.")
                return None
            else:
                # Create a new symbol with a generated UUID
                pst = pytz.timezone('America/Los_Angeles')
                current_time = datetime.now(pst)
                new_symbol = Symbol(
                    symbol_id=uuid.uuid4(), 
                    symbol=symbol, 
                    last_updated_at=current_time
                )
                session.add(new_symbol)
                session.commit()
                # Refresh the object to ensure all attributes are loaded
                session.refresh(new_symbol)
                print(f"Symbol '{symbol}' added successfully.")
                return new_symbol
    except Exception as e:
        print(f"Error adding symbol '{symbol}': {str(e)}")
        return None