import uuid
import pandas as pd
import os
from decimal import Decimal
from sqlalchemy.orm import Session
from typing import Dict, List
from ..models import Symbol, Sector, SymbolSector

def get_csv_path() -> str:
    """Return the path to the symbol_sector_industry.csv file"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'symbol_sector_industry.csv')

def populate_sector_tables(session: Session) -> Dict:
    """
    Populate sectors and symbol_sectors tables using data from symbol_sector_industry.csv
    
    Args:
        session (Session): Database session
        
    Returns:
        Dict: Results of the operation
    """
    try:
        # Read the CSV
        csv_path = get_csv_path()
        df = pd.read_csv(csv_path)
        
        # Get unique sectors and create entries with UUIDs
        unique_sectors = df['yfinance Sector'].unique()
        
        sector_map = {}  # To store sector_name -> sector_id mapping
        
        # Create sector records
        for sector in unique_sectors:
            sector_id = uuid.uuid4()
            new_sector = Sector(
                sector_id=sector_id,
                sector_name=sector
            )
            session.add(new_sector)
            sector_map[sector] = sector_id
        
        # Commit to get the sector IDs
        session.commit()
        
        # Get all symbols from the database to map ticker -> symbol_id
        symbols = session.query(Symbol.symbol, Symbol.symbol_id).all()
        symbol_map = {s.symbol: s.symbol_id for s in symbols}
        
        # Create symbol_sector entries
        symbols_linked = 0
        symbols_skipped = 0
        skipped_symbols: List[str] = []
        
        for _, row in df.iterrows():
            ticker = row['symbol']
            sector = row['yfinance Sector']
            
            if ticker in symbol_map and sector in sector_map:
                symbol_sector = SymbolSector(
                    symbol_id=symbol_map[ticker],
                    sector_id=sector_map[sector],
                    pct=Decimal('1.0')  # 100% allocation to the sector
                )
                session.add(symbol_sector)
                symbols_linked += 1
            else:
                if ticker not in symbol_map:
                    skipped_symbols.append(ticker)
                symbols_skipped += 1
        
        # Commit the symbol_sector entries
        session.commit()
        
        return {
            "status": "success",
            "message": f"Successfully populated sector tables",
            "sectors_added": len(unique_sectors),
            "symbols_linked": symbols_linked,
            "symbols_skipped": symbols_skipped,
            "skipped_symbols": skipped_symbols[:10]  # Only include first 10 for brevity
        }
    
    except Exception as e:
        session.rollback()
        return {
            "status": "error",
            "message": f"Failed to populate sector tables: {str(e)}"
        } 