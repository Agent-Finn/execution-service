from fastapi import APIRouter, HTTPException
from typing import Optional
from ..service.add_sector import add_sector

router = APIRouter(
    prefix="/create-sector",
    tags=["Utils"]
)

@router.post("/", response_model=dict)
async def create_sector(sector: str):
    """
    Add a new sector to the sectors table if it doesn't already exist.

    Args:
        sector (str): The name of the sector to add (e.g., "Technology")

    Returns:
        dict: A dictionary containing the sector_id and sector_name if added,
              or a message if the sector already exists

    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        result = add_sector(sector)
        if result:
            return {
                "sector_id": str(result.sector_id),  # Convert UUID to string for JSON
                "sector_name": result.sector_name
            }
        else:
            return {"message": f"Sector '{sector}' already exists or could not be added"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error adding sector '{sector}': {str(e)}"
        )