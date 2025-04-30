from .get_stock_price_router import get_stock_price
from ..database import SessionLocal
from ..models import Symbol
from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter(tags=["Partial Trades"])

@router.get("/update-stock-price/{symbol}")
async def update_stock_price(symbol: str, date: str = None):
    try:
        # Get current date if no date provided
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        # Get the stock price - add await here
        price = await get_stock_price(symbol, date)
        
        if price == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No price data found for symbol {symbol} on {date}"
            )
        
        # Update the stock price in the database
        with SessionLocal() as session:
            symbol_record = session.query(Symbol).filter(Symbol.symbol == symbol).first()
            
            
            if not symbol_record:
                raise HTTPException(
                    status_code=404,
                    detail=f"Symbol {symbol} not found in database"
                )
                
            current_time = datetime.now()
            # symbol_record.price = price (removed as price field no longer exists in Symbol model)
            symbol_record.last_updated = current_time
            symbol_record.last_updated_at = current_time
            session.commit()
            
            return {
                "symbol": symbol,
                "price": price,
                "date": date,
                "last_updated": symbol_record.last_updated
            }
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update stock price: {str(e)}"
        )

