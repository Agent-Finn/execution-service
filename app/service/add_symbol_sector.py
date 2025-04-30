from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import SymbolSector, Symbol, Sector
from typing import Optional, Dict
import uuid
from decimal import Decimal
from sqlalchemy import func

def add_symbol_sector(symbol_name: str, sector_name: str, pct: float) -> Optional[Dict]:
    """
    Add a symbol-sector relationship to the symbol_sectors table.
    
    Args:
        symbol_name (str): The symbol (e.g., "AAPL")
        sector_name (str): The name of the sector
        pct (float): The percentage allocation to the sector (0-1)
        
    Returns:
        Optional[Dict]: A dictionary with the created record details if successful, None otherwise
    """
    try:
        with SessionLocal() as session:
            # Find the symbol by name
            symbol = session.query(Symbol).filter(Symbol.symbol == symbol_name).first()
            if not symbol:
                print(f"Symbol '{symbol_name}' does not exist.")
                return None
            
            symbol_id = symbol.symbol_id
                
            # Find the sector by name
            sector = session.query(Sector).filter(Sector.sector_name == sector_name).first()
            if not sector:
                print(f"Sector with name '{sector_name}' does not exist.")
                return None
            
            sector_id = sector.sector_id
            
            # Check if the relationship already exists
            existing = session.query(SymbolSector).filter(
                SymbolSector.symbol_id == symbol_id,
                SymbolSector.sector_id == sector_id
            ).first()
            
            # Calculate current total percentage for this symbol (excluding this sector if updating)
            if existing:
                current_total = session.query(func.sum(SymbolSector.pct)).filter(
                    SymbolSector.symbol_id == symbol_id,
                    SymbolSector.sector_id != sector_id
                ).scalar() or Decimal('0')
            else:
                current_total = session.query(func.sum(SymbolSector.pct)).filter(
                    SymbolSector.symbol_id == symbol_id
                ).scalar() or Decimal('0')
            
            # Check if adding this percentage would exceed 1
            new_total = current_total + Decimal(str(pct))
            if abs(new_total - Decimal('1')) > Decimal('0.0001'):
                print(f"Total percentage would be {new_total}, which is not equal to 1.")
                return None
            
            if existing:
                # Update the existing record
                existing.pct = Decimal(pct)
                session.commit()
                session.refresh(existing)
                return {
                    "symbol": symbol_name,
                    "symbol_id": str(existing.symbol_id),
                    "sector": sector_name,
                    "sector_id": str(existing.sector_id),
                    "pct": float(existing.pct),
                    "action": "updated",
                    "total_pct": float(new_total)
                }
            else:
                # Create a new record
                new_symbol_sector = SymbolSector(
                    symbol_id=symbol_id,
                    sector_id=sector_id,
                    pct=Decimal(pct)
                )
                session.add(new_symbol_sector)
                session.commit()
                
                return {
                    "symbol": symbol_name,
                    "symbol_id": str(new_symbol_sector.symbol_id),
                    "sector": sector_name,
                    "sector_id": str(new_symbol_sector.sector_id),
                    "pct": float(new_symbol_sector.pct),
                    "action": "created",
                    "total_pct": float(new_total)
                }
    except Exception as e:
        print(f"Error adding symbol-sector relationship: {str(e)}")
        return None 