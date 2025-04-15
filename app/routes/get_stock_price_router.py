from fastapi import APIRouter, HTTPException
from ..stock_prices import AlpacaService

router = APIRouter(
    prefix="/get_stock-prices",
    tags=["Utils"],
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
        float: The closing price of the stock, or 0 if no data is available.

    Raises:
        HTTPException: 400 for invalid date format, 500 for other errors.
    """
    try:
        # Initialize the Alpaca service
        service = AlpacaService()

        # If no date provided, raise error
        if not date:
            raise HTTPException(
                status_code=400,
                detail="Date parameter is required (format: YYYY-MM-DD)"
            )

        # Try to get historical price for the specific date
        try:
            price_data = service.get_historical_price(symbol, date)
        except HTTPException as he:
            if he.status_code == 403:
                # Fallback to 2024-02-20 if 403 Forbidden is received
                price_data = service.get_historical_price(symbol, "2024-02-20")
            else:
                raise he  # Re-raise other HTTP exceptions

        if not price_data:
            return 0

        # Return just the closing price
        return price_data["c"]

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}. Use YYYY-MM-DD")
    except HTTPException as he:
        raise he  # Re-raise HTTP exceptions from service
    except Exception as e:
        print(f"Error fetching stock prices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock prices: {str(e)}")