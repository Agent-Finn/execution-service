from fastapi import APIRouter, HTTPException
from ..stock_prices import AlpacaService  # Import the new service class

router = APIRouter(
    prefix="/stock-prices",
    tags=["stock_prices"],
    responses={404: {"description": "Stock not found or invalid parameters"}},
)

@router.get("/{symbol}")
async def get_stock_price(symbol: str, date: str = None):
    """
    Fetch stock price for a given symbol and specific date.

    Args:
        symbol (str): The stock ticker symbol (e.g., "AAPL").
        date (str, optional): Date for historical data (YYYY-MM-DD). Defaults to None.

    Returns:
        dict: A price entry with "date" and "price" keys wrapped in a "prices" list.

    Raises:
        HTTPException: 404 if the symbol is invalid or no data is available, 400 for invalid date format,
                      500 for other errors.
    """
    try:
        # Initialize the Alpaca service
        service = AlpacaService()

        # If no date provided, we could add current price logic later if needed
        if not date:
            raise HTTPException(
                status_code=400,
                detail="Date parameter is required (format: YYYY-MM-DD)"
            )

        # Get historical price for the specific date
        price_data = service.get_historical_price(symbol, date)
        
        if not price_data:
            raise HTTPException(
                status_code=404,
                detail=f"No price data available for {symbol} on {date}"
            )

        # Format the response to match your expected structure
        price_entry = {
            "date": price_data["t"].split("T")[0],  # Extract YYYY-MM-DD from timestamp
            "price": price_data["c"]  # Using closing price
        }
        
        return {"prices": [price_entry]}

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}. Use YYYY-MM-DD")
    except HTTPException as he:
        raise he  # Re-raise HTTP exceptions from service
    except Exception as e:
        print(f"Error fetching stock prices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock prices: {str(e)}")
