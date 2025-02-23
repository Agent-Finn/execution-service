from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from ..database import engine

router = APIRouter()

@router.get("/portfolio-value")
async def get_portfolio_value():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT portfolio_value FROM portfolio_stats ORDER BY created_at DESC LIMIT 1"))
            row = result.fetchone()
            
            if row is None:
                raise HTTPException(status_code=404, detail="No portfolio value found")
                
            return {"portfolio_value": row[0]}
    except Exception as e:
        print(f"Failed to fetch portfolio value: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 