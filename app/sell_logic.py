from typing import List, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session
import logging
from pydantic import BaseModel, EmailStr
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base
from .database import SessionLocal
from .models import Trade, Allocation, Position
from .stock_prices import AlpacaService
from uuid import UUID
# SQLAlchemy Base
Base = declarative_base()

class ExecutionService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_allocations_by_portfolio(self, db: Session, portfolio_id: UUID) -> Dict:
        """
        Fetch all allocations for a given portfolio_id.
        """
        try:
            allocations = db.query(Allocation).filter(Allocation.portfolio_id == portfolio_id).all()
            
            if not allocations:
                raise HTTPException(status_code=404, detail=f"No allocations found for portfolio_id {portfolio_id}")
            
            allocations_list = [
                {
                    "allocation_id": alloc.allocation_id,
                    "portfolio_id": alloc.portfolio_id,
                    "recommendation_date": alloc.recommendation_date.isoformat() if alloc.recommendation_date else None,
                    "symbol": alloc.symbol,
                    "target_pct": float(alloc.target_pct) if alloc.target_pct is not None else None
                }
                for alloc in allocations
            ]
            return {"allocations": allocations_list}
        except HTTPException as he:
            raise he
        except Exception as e:
            self.logger.error(f"Failed to fetch allocations: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch allocations: {str(e)}")

    def get_portfolio_positions(self, db: Session, portfolio_id: UUID) -> Dict:
        """
        Fetch all current positions for a given portfolio_id.
        """
        try:
            positions = db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
            
            if not positions:
                return {"positions": []}
            
            positions_list = [
                {
                    "position_id": pos.position_id,
                    "portfolio_id": pos.portfolio_id,
                    "user_id": pos.user_id,
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "last_updated": pos.last_updated.isoformat() if pos.last_updated else None
                }
                for pos in positions
            ]
            return {"positions": positions_list}
        except Exception as e:
            self.logger.error(f"Failed to fetch positions: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")

    def determine_stocks_to_sell(self, db: Session, portfolio_id: UUID) -> List[Dict]:
        """
        Compare current positions with allocations and determine stocks to sell.
        
        Returns:
            List of positions that should be sold (not in allocations)
        """
        try:
            # Get current allocations and positions
            allocations_data = self.get_allocations_by_portfolio(db, portfolio_id)
            positions_data = self.get_portfolio_positions(db, portfolio_id)

            # Extract symbols from allocations
            allocated_symbols = {alloc["symbol"] for alloc in allocations_data["allocations"]}

            # Find positions that aren't in the allocations
            stocks_to_sell = [
                position for position in positions_data["positions"]
                if position["symbol"] not in allocated_symbols
            ]

            self.logger.info(f"Found {len(stocks_to_sell)} stocks to sell for portfolio {portfolio_id}")
            return stocks_to_sell

        except Exception as e:
            self.logger.error(f"Error determining stocks to sell: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing execution: {str(e)}")

    def execute_sell_orders(self, db: Session, portfolio_id: UUID) -> Dict:
        """
        Execute the selling of stocks that aren't in the current allocations by writing to the trades table.
        
        Returns:
            Dict with execution results including stocks sold
        """
        try:
            stocks_to_sell = self.determine_stocks_to_sell(db, portfolio_id)
            
            if not stocks_to_sell:
                return {
                    "status": "success",
                    "message": "No stocks to sell",
                    "stocks_sold": []
                }

            # List to store executed trades
            executed_trades = []
            service = AlpacaService()
            current_date = '2024-02-20' #datetime.now().strftime("%Y-%m-%d")

            # Record each sell trade in the trades table
            for stock in stocks_to_sell:
                trade = Trade(
                    portfolio_id=stock["portfolio_id"],
                    user_id=stock["user_id"],
                    trade_time=datetime.utcnow(),  # Use current UTC time
                    symbol=stock["symbol"],
                    sector="Technology",  # Assuming sector isn't available in positions; you might need to fetch this
                    trade_type="SELL",
                    order_type="MARKET",
                    price=service.get_historical_price(stock["symbol"], current_date)["c"],  # Market order, price will be determined by the exchange
                    quantity=stock["quantity"], 
                    value=service.get_historical_price(stock["symbol"], current_date)["c"] * stock["quantity"], 
                    reason="Portfolio rebalancing"  # Sell all shares held
                )
                db.add(trade)
                executed_trades.append({
                    "trade_id": trade.trade_id,  # This will be set after commit
                    "symbol": trade.symbol,
                    "quantity": trade.quantity,
                    "portfolio_id": trade.portfolio_id,
                    "user_id": trade.user_id
                })

            # Commit the transaction
            db.commit()

            # Optionally, you could update the positions table to reflect the sold quantities,
            # but I'll leave that out for now as per your request to focus on trades.

            return {
                "status": "success",
                "message": f"Executed {len(executed_trades)} sell orders",
                "stocks_sold": executed_trades
            }

        except Exception as e:
            db.rollback()  # Roll back in case of error
            self.logger.error(f"Error executing sell orders: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error executing sell orders: {str(e)}")