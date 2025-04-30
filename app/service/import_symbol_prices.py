import uuid
import pandas as pd
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
import pytz
from ..database import SessionLocal
from ..models import Symbol, SymbolPrice
from .utils import get_symbol_id

async def import_symbol_prices_from_csv(file_path: str) -> Dict:
    """
    Import historical price data from a CSV file into the symbol_prices table.
    
    Args:
        file_path (str): Path to the CSV file containing price data
        
    Returns:
        Dict: A dictionary containing the results of the import operation
    """
    result = {
        "status": "success",
        "total_processed": 0,
        "successfully_imported": 0,
        "already_exists": 0,
        "errors": 0,
        "error_details": []
    }
    
    try:
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        # Check if required columns exist
        required_columns = ['symbol', 'date', 'open']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "status": "error",
                "message": f"Missing required columns: {', '.join(missing_columns)}"
            }
        
        # Process the data
        symbol_name = df['symbol'].iloc[0]  # Assuming the CSV contains data for a single symbol
        
        with SessionLocal() as session:
            # Get symbol_id for the ticker
            symbol_id = get_symbol_id(session, symbol_name)
            
            if not symbol_id:
                return {
                    "status": "error",
                    "message": f"Symbol '{symbol_name}' does not exist in the database. Please add it first."
                }
            
            # Process each row in the CSV
            for _, row in df.iterrows():
                result["total_processed"] += 1
                
                try:
                    # Convert date string to date object
                    price_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                    
                    # Check if this price entry already exists
                    existing_price = session.query(SymbolPrice).filter(
                        SymbolPrice.symbol_id == symbol_id,
                        SymbolPrice.price_at == price_date
                    ).first()
                    
                    if existing_price:
                        result["already_exists"] += 1
                        continue
                    
                    # Create a new price entry
                    new_price = SymbolPrice(
                        symbol_id=symbol_id,
                        price=Decimal(str(row['open'])),  # Use open price
                        price_at=price_date
                    )
                    
                    session.add(new_price)
                    result["successfully_imported"] += 1
                
                except Exception as e:
                    result["errors"] += 1
                    result["error_details"].append({
                        "date": row['date'],
                        "error": str(e)
                    })
            
            # Commit the changes
            session.commit()
        
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error importing data: {str(e)}"
        } 