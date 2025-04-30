from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from ..service.add_symbol import add_symbol

router = APIRouter(
    tags=["Utils"]
)

class SymbolList(BaseModel):
    symbols: List[str]

@router.post("/", response_model=dict)
async def create_symbol(symbols_data: SymbolList):
    """
    Add new symbols to the symbols table if they don't already exist.

    Args:
        symbols_data (SymbolList): List of symbols to add (e.g., ["AAPL", "MSFT", "GOOGL"])

    Returns:
        dict: A dictionary containing the results of the operation

    Raises:
        HTTPException: If there's an error processing the request
    """
    results = {
        "added": [],
        "existing": [],
        "failed": []
    }
    
    try:
        for symbol in symbols_data.symbols:
            result = await add_symbol(symbol)
            if result:
                results["added"].append({
                    "symbol_id": str(result.symbol_id),
                    "symbol": result.symbol
                })
            else:
                results["existing"].append(symbol)
        
        return {
            "message": f"Processed {len(symbols_data.symbols)} symbols",
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing symbols: {str(e)}"
        )