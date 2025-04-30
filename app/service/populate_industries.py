import uuid
import pandas as pd
import os
from decimal import Decimal
from sqlalchemy.orm import Session
from typing import Dict, List
from ..models import Symbol, Industry, SymbolIndustry

def get_csv_path() -> str:
    """Return the path to the symbol_sector_industry.csv file"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'symbol_sector_industry.csv')

def populate_industry_tables(session: Session) -> Dict:
    """
    Populate industries and symbol_industries tables using data from symbol_sector_industry.csv
    
    Args:
        session (Session): Database session
        
    Returns:
        Dict: Results of the operation
    """
    try:
        # Read the CSV
        csv_path = get_csv_path()
        df = pd.read_csv(csv_path)
        
        # Get unique industries and create entries with UUIDs
        unique_industries = df['yfinance Industry'].unique()
        
        industry_map = {}  # To store industry_name -> industry_id mapping
        
        # Create industry records
        for ind in unique_industries:
            ind_id = uuid.uuid4()
            new_industry = Industry(
                industry_id=ind_id,
                industry=ind
            )
            session.add(new_industry)
            industry_map[ind] = ind_id
        
        # Commit to get the industry IDs
        session.commit()
        
        # Get all symbols from the database to map ticker -> symbol_id
        symbols = session.query(Symbol.symbol, Symbol.symbol_id).all()
        symbol_map = {s.symbol: s.symbol_id for s in symbols}
        
        # Create symbol_industry entries
        symbols_linked = 0
        symbols_skipped = 0
        skipped_symbols: List[str] = []
        
        for _, row in df.iterrows():
            ticker = row['symbol']
            industry = row['yfinance Industry']
            
            if ticker in symbol_map and industry in industry_map:
                symbol_industry = SymbolIndustry(
                    symbol_id=symbol_map[ticker],
                    industry_id=industry_map[industry],
                    pct=Decimal('1.0')  # 100% allocation to the industry
                )
                session.add(symbol_industry)
                symbols_linked += 1
            else:
                if ticker not in symbol_map:
                    skipped_symbols.append(ticker)
                symbols_skipped += 1
        
        # Commit the symbol_industry entries
        session.commit()
        
        return {
            "status": "success",
            "message": f"Successfully populated industry tables",
            "industries_added": len(unique_industries),
            "symbols_linked": symbols_linked,
            "symbols_skipped": symbols_skipped,
            "skipped_symbols": skipped_symbols[:10]  # Only include first 10 for brevity
        }
    
    except Exception as e:
        session.rollback()
        return {
            "status": "error",
            "message": f"Failed to populate industry tables: {str(e)}"
        } 