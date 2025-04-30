import requests
import time
from typing import List, Dict, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Symbol, SymbolSector, Sector
from .add_symbol_sector import add_symbol_sector

# Alpha Vantage API settings
ALPHA_VANTAGE_API_KEY = "9UWQE3DBFDE0IM2V"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_RATE_LIMIT = 2  # seconds between calls to avoid rate limiting (5 calls per minute)

def get_sector_from_alpha_vantage(symbol: str) -> Optional[str]:
    """
    Get sector information for a symbol using Alpha Vantage API.
    
    Args:
        symbol (str): The stock symbol (e.g., "AAPL")
        
    Returns:
        Optional[str]: The sector name if found, None otherwise
    """
    try:
        # Prepare request
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        # Make API request
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract sector
        if "Sector" in data and data["Sector"]:
            # Normalize case - convert from uppercase to title case
            sector = data["Sector"].title()
            print(f"Normalized sector for {symbol}: {data['Sector']} → {sector}")
            return sector
        else:
            print(f"No sector information found for {symbol}")
            return None
            
    except Exception as e:
        print(f"Error getting sector for {symbol}: {str(e)}")
        return None

def process_symbols_batch(symbols: List[str]) -> Dict[str, str]:
    """
    Process a batch of symbols and get their sectors from Alpha Vantage.
    
    Args:
        symbols (List[str]): List of symbol names
        
    Returns:
        Dict[str, str]: Dictionary mapping symbols to their sectors
    """
    result = {}
    total = len(symbols)
    print(f"Processing {total} symbols in batch with Alpha Vantage API...")
    
    for i, symbol in enumerate(symbols):
        print(f"Processing symbol {i+1}/{total}: {symbol}")
        sector = get_sector_from_alpha_vantage(symbol)
        
        if sector:
            result[symbol] = sector
            print(f"Found sector for {symbol}: {sector}")
        
        # Sleep to avoid rate limiting (except for the last item)
        if i < total - 1:
            print(f"Waiting {ALPHA_VANTAGE_RATE_LIMIT} seconds to avoid rate limiting...")
            time.sleep(ALPHA_VANTAGE_RATE_LIMIT)
    
    print(f"Completed API calls. Found sectors for {len(result)}/{total} symbols.")
    return result

def populate_symbol_sectors(symbols: List[str], batch_size: int = 5) -> Dict:
    """
    Populate the symbol_sectors table with sector information for the given symbols.
    
    Args:
        symbols (List[str]): List of symbol names to process
        batch_size (int): Number of symbols to process in each batch
        
    Returns:
        Dict: Summary of the operation with counts of successes and failures
    """
    result = {
        "processed": 0,
        "added": 0,
        "skipped": 0,
        "failed": 0,
        "missing_sectors": [],
        "errors": []
    }
    
    try:
        with SessionLocal() as session:
            # Step 1: Check which symbols exist in the database and don't have sector assignments
            symbols_to_process = []
            symbol_records = {}
            
            for symbol_name in symbols:
                try:
                    # Check if symbol exists in the database
                    symbol = session.query(Symbol).filter(Symbol.symbol == symbol_name).first()
                    if not symbol:
                        result["failed"] += 1
                        result["errors"].append(f"Symbol {symbol_name} does not exist in the database")
                        continue
                    
                    # Check if symbol already has sector assignments
                    existing_assignments = session.query(SymbolSector).filter(
                        SymbolSector.symbol_id == symbol.symbol_id
                    ).first()
                    
                    if existing_assignments:
                        result["skipped"] += 1
                        continue
                    
                    # Add to list of symbols to process
                    symbols_to_process.append(symbol_name)
                    symbol_records[symbol_name] = symbol
                    
                except Exception as e:
                    result["failed"] += 1
                    result["errors"].append(f"Error checking {symbol_name}: {str(e)}")
            
            # Early exit if no symbols need processing
            if not symbols_to_process:
                return result
                
            # Step 2: Process symbols in smaller batches
            symbols_to_process_count = len(symbols_to_process)
            print(f"Found {symbols_to_process_count} symbols that need sector data")
            
            # Process in batches
            for i in range(0, symbols_to_process_count, batch_size):
                batch = symbols_to_process[i:i+batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(symbols_to_process_count+batch_size-1)//batch_size}")
                
                # Get sector information for this batch
                sector_data = process_symbols_batch(batch)
                
                # Step 3: Process the results and add to the database
                for symbol_name in batch:
                    result["processed"] += 1
                    
                    if symbol_name not in sector_data:
                        result["failed"] += 1
                        result["missing_sectors"].append(symbol_name)
                        continue
                    
                    sector_name = sector_data[symbol_name]
                    
                    # Add the symbol-sector relationship (100% allocation to the sector)
                    add_result = add_symbol_sector(symbol_name, sector_name, 1.0)
                    
                    if add_result:
                        result["added"] += 1
                    else:
                        result["failed"] += 1
                        result["errors"].append(f"Failed to add sector for {symbol_name}")
        
        return result
    
    except Exception as e:
        print(f"Error in populate_symbol_sectors: {str(e)}")
        result["errors"].append(f"Global error: {str(e)}")
        return result 