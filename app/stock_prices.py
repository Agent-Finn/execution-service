import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict

class AlpacaService:
    def __init__(self):
        self.api_key_id = os.environ["ALPACA_API_KEY_ID"]
        self.api_secret_key = os.environ["ALPACA_API_SECRET_KEY"]
        self.base_url = "https://data.alpaca.markets/v2/stocks"
        self.headers = {
            "APCA-API-KEY-ID": self.api_key_id,
            "APCA-API-SECRET-KEY": self.api_secret_key,
            "Content-Type": "application/json"
        }

    def get_historical_price(self, ticker: str, date: str) -> Optional[Dict]:
        """
        Get historical price for a specific ticker and date.
        
        Args:
            ticker (str): Stock ticker symbol (e.g., "TSLA")
            date (str): Date in YYYY-MM-DD format
            
        Returns:
            dict: Price data containing close price and other info, or None if request fails
        """
        try:
            # Parse input date and create end date (next day)
            start_date = datetime.strptime(date, "%Y-%m-%d")
            end_date = start_date + timedelta(days=1)
            
            # Format dates to ISO 8601 as in your curl example
            start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
            end_str = end_date.strftime("%Y-%m-%dT00:00:00Z")
            
            # Construct the URL
            url = f"{self.base_url}/{ticker.upper()}/bars"
            params = {
                "start": start_str,
                "end": end_str,
                "limit": 1,
                "timeframe": "1Day"
            }
            
            # Make the API request
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()  # Raise exception for bad status codes
            
            data = response.json()
            if "bars" in data and data["bars"]:
                return data["bars"][0]  # Return first (and only) bar
            return None
            
        except ValueError as e:
            print(f"Invalid date format: {e}. Please use YYYY-MM-DD")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

# Example usage
if __name__ == "__main__":
    # Make sure your environment variables are set
    service = AlpacaService()
    
    # Test the service
    ticker = "TSLA"
    date = "2024-06-03"
    price_data = service.get_historical_price(ticker, date)
    
    if price_data:
        print(f"Price data for {ticker} on {date}:")
        print(f"Close: {price_data['c']}")
        print(f"Open: {price_data['o']}")
        print(f"High: {price_data['h']}")
        print(f"Low: {price_data['l']}")
        print(f"Volume: {price_data['v']}")
        print(f"Timestamp: {price_data['t']}")
    else:
        print("No data returned")