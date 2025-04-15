from fastapi import APIRouter, HTTPException
from typing import Optional
from ..service.add_symbol import add_symbol

router = APIRouter(
    tags=["Utils"]
)

@router.post("/", response_model=dict)
async def create_symbol(symbol: str):
    """
    Add a new symbol to the symbols table if it doesn't already exist.

    Args:
        symbol (str): The name of the symbol to add (e.g., "Technology")

    Returns:
        dict: A dictionary containing the symbol_id and symbol if added,
              or a message if the symbol already exists

    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        result = await add_symbol(symbol)
        if result:
            return {
                "symbol_id": str(result.symbol_id),  # Convert UUID to string for JSON
                "symbol": result.symbol
            }
        else:
            return {"message": f"symbol '{symbol}' already exists or could not be added"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error adding symbol '{symbol}': {str(e)}"
        )