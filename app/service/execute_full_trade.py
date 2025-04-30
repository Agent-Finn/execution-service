import uuid
from datetime import datetime, date, timedelta, time, timezone
import pytz
from typing import Dict, List, Optional, Tuple
from sqlalchemy import desc, text, func, Date
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Position, Allocation, Trade, Symbol, PortfolioStats, SymbolPrice
from .utils import get_symbol_id, get_symbol_price, get_symbol_name
from decimal import Decimal
import numpy as np
import pandas as pd

BUY = "Buy"
SELL = "Sell"
ORDER_TYPE = "Market"
REASON = "Portfolio rebalancing"

async def execute_full_trade(allocation_batch_id: uuid.UUID) -> Dict:
    """
    Execute a full trade based on a portfolio's allocation batch and current positions.
    
    Args:
        allocation_batch_id (uuid.UUID): The batch ID for the allocations to use
    
    Returns:
        Dict: A dictionary containing the results of the trade execution
    """
    try:
        with SessionLocal() as session:
            session.expire_all()
            
            # 1. Get allocations for the given batch ID
            allocations = session.query(Allocation).filter(
                Allocation.allocation_batch_id == allocation_batch_id
            ).all()
            
            if not allocations:
                return {"status": "error", "message": f"No allocations found for batch ID {allocation_batch_id}"}
            
            # Get the portfolio ID from the first allocation (all allocations in batch should have the same portfolio)
            portfolio_id = allocations[0].portfolio_id
            
            # Get the allocated_at timestamp from the first allocation
            allocated_at = allocations[0].allocated_at
            
            if not allocated_at:
                return {"status": "error", "message": f"No allocation timestamp found for batch ID {allocation_batch_id}"}
            
            # Convert timestamp to date object for price lookup
            trade_date = allocated_at.date()
            
            # Get latest portfolio stats to find portfolio balance
            latest_stats = session.query(PortfolioStats).filter(
                PortfolioStats.portfolio_id == portfolio_id,
                PortfolioStats.recorded_at <= allocated_at
            ).order_by(desc(PortfolioStats.recorded_at)).first()
            
            if not latest_stats:
                return {"status": "error", "message": f"No portfolio stats found for portfolio ID {portfolio_id}"}
            
            portfolio_balance = float(latest_stats.portfolio_balance)
            
            if portfolio_balance <= 0:
                return {"status": "error", "message": f"Invalid portfolio balance: ${portfolio_balance:.2f}"}
            
            # 3. Get current positions for the portfolio (latest recorded_at)
            latest_positions = get_latest_positions(session, portfolio_id)
            
            # Price date is the same as trade date
            price_date = trade_date
            
            # 4. Calculate what to buy and sell using the trade date prices
            trades_to_execute = await calculate_trades(session, allocations, latest_positions, price_date, portfolio_balance)
            
            # Print out planned buys and sells
            print(f"\nPlanned Trades for Portfolio {portfolio_id}, Batch {allocation_batch_id} on {trade_date}:")
            print(f"Portfolio Balance: ${portfolio_balance:.2f} (tracked as a position)")
            
            buy_trades = [t for t in trades_to_execute if t["trade_type"] == BUY]
            sell_trades = [t for t in trades_to_execute if t["trade_type"] == SELL]
            
            if buy_trades:
                print("\nPLANNED BUYS:")
                for trade in buy_trades:
                    symbol = get_symbol_name(session, trade["symbol_id"])
                    price = float(trade["price"])
                    quantity = float(trade["quantity"])
                    total = price * quantity
                    print(f"BUY {quantity} shares of {symbol} at ${price:.2f} = ${total:.2f}")
            
            if sell_trades:
                print("\nPLANNED SELLS:")
                for trade in sell_trades:
                    symbol = get_symbol_name(session, trade["symbol_id"])
                    price = float(trade["price"])
                    quantity = float(trade["quantity"])
                    total = price * quantity
                    print(f"SELL {quantity} shares of {symbol} at ${price:.2f} = ${total:.2f}")
            
            # Convert trades to response format without executing
            planned_trades = []
            for trade in trades_to_execute:
                planned_trades.append({
                    "trade_id": "planned-" + str(uuid.uuid4()),
                    "portfolio_id": str(trade["portfolio_id"]),
                    "symbol_id": str(trade["symbol_id"]),
                    "symbol": get_symbol_name(session, trade["symbol_id"]),
                    "trade_type": trade["trade_type"],
                    "quantity": trade["quantity"],
                    "price": float(trade["price"]),
                    "total_value": float(trade["price"] * trade["quantity"])
                })
            
            # 5. Execute trades
            executed_trades = await execute_trades(session, trades_to_execute, trade_date.strftime("%Y-%m-%d"))
        
            
            return {
                "status": "success",
                "message": f"Executed {len(executed_trades)} trades",
                "portfolio_id": str(portfolio_id),
                "allocation_batch_id": str(allocation_batch_id),
                "initial_portfolio_balance": portfolio_balance,
                "trade_date": trade_date.strftime("%Y-%m-%d"),
                "executed_trades": executed_trades
            }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error planning full trade: {str(e)}")
        return {"status": "error", "message": f"Error planning full trade: {str(e)}"}




def get_latest_positions(session: Session, portfolio_id: uuid.UUID) -> List[Position]:
    # Get distinct symbol_ids in the portfolio
    symbol_ids = session.query(Position.symbol_id).filter(
        Position.portfolio_id == portfolio_id
    ).distinct().all()
    
    # For each symbol_id, get the latest position
    latest_positions = []
    for (symbol_id,) in symbol_ids:
        latest_position = session.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.symbol_id == symbol_id
        ).order_by(desc(Position.recorded_at)).first()
        
        if latest_position:
            latest_positions.append(latest_position)
    
    return latest_positions

async def calculate_trades(
    session: Session, 
    allocations: List[Allocation], 
    positions: List[Position], 
    price_date: date,
    portfolio_balance: float
) -> List[Dict]:
    """
    Calculate what trades need to be executed based on allocations and current positions.
    
    Logical flow:
    1. Calculate how many of each stock we need given allocations and portfolio value
    2. Sell the stocks we do not need at given day's price
    3. Buy the remained of the stocks at given day's price
    
    Args:
        session (Session): The database session
        allocations (List[Allocation]): The list of allocations
        positions (List[Position]): The list of current positions
        price_date (date): The date for price lookup
        portfolio_balance (float): The current portfolio balance from portfolio_stats
        
    Returns:
        List[Dict]: A list of trades to execute
    """
    trades_to_execute = []
    portfolio_id = allocations[0].portfolio_id
    
    # Create a map of current positions by symbol_id
    positions_map = {position.symbol_id: position for position in positions}
    
    # Create a map of target allocations by symbol_id
    allocations_map = {allocation.symbol_id: allocation for allocation in allocations}
    
    # Get total portfolio value from portfolio_stats
    total_portfolio_value = await calculate_positions_value(session, portfolio_id, price_date)
    print(f"\nPortfolio Balance: ${total_portfolio_value:.2f}")
    print(f"Total Portfolio Value: ${total_portfolio_value:.2f}")
    
    # Check and print allocation percentages
    total_allocation_pct = Decimal('0')
    for allocation in allocations:
        total_allocation_pct += Decimal(str(allocation.allocation_pct))
    
    print(f"DEBUG: Total allocation percentage: {float(total_allocation_pct)*100:.4f}%")
    
    # STEP 1: Calculate target quantities directly based on allocations
    # These are the shares we SHOULD own based on the portfolio value and allocations
    target_quantities = {}
    for symbol_id, allocation in allocations_map.items():
        # Calculate target value based on allocation percentage and TOTAL PORTFOLIO VALUE
        allocation_pct = Decimal(str(allocation.allocation_pct))
        total_value_decimal = Decimal(str(total_portfolio_value))
        target_value = total_value_decimal * allocation_pct
        
        price = get_symbol_price(session, symbol_id, price_date)
        price_decimal = Decimal(str(price))
        symbol_name = get_symbol_name(session, symbol_id)
        
        # Skip if price is zero to avoid division by zero
        if price_decimal == Decimal('0'):
            print(f"DEBUG: Skipping {symbol_name} due to zero price")
            continue
        
        # Calculate target quantity - how many shares should we own total
        target_quantity = target_value / price_decimal
        target_quantity = target_quantity.quantize(Decimal('0.0001'), rounding='ROUND_HALF_UP')
        
        # Store target quantity in map
        target_quantities[symbol_id] = {
            "symbol_id": symbol_id,
            "symbol_name": symbol_name,
            "price": price_decimal,
            "target_quantity": target_quantity,
            "target_value": target_value,
            "allocation_pct": allocation_pct,
            "current_quantity": Decimal('0') if symbol_id not in positions_map else Decimal(str(positions_map[symbol_id].quantity))
        }
        
        print(f"DEBUG: {symbol_name} - Target: {target_quantity} shares (${float(target_value):.2f}, {float(allocation_pct)*100:.2f}%), Current: {target_quantities[symbol_id]['current_quantity']}")
    
    # Verify total target value
    total_target_value = sum(data["target_value"] for data in target_quantities.values())
    print(f"DEBUG: Total target value: ${float(total_target_value):.2f}")
    
    # STEP 2: Generate sell trades for stocks not in allocations or that need reduction
    sell_trades = []
    
    # First, sell positions not in the allocations
    for symbol_id, position in positions_map.items():
        current_quantity = Decimal(str(position.quantity))
        
        if current_quantity <= Decimal('0'):
            continue
            
        # If symbol is not in allocations, sell entire position
        if symbol_id not in allocations_map:
            price_decimal = Decimal(str(get_symbol_price(session, symbol_id, price_date)))
            symbol_name = get_symbol_name(session, symbol_id)
            
            print(f"DEBUG: Selling entire position of {symbol_name}: {current_quantity} shares at ${float(price_decimal)}")
            
            sell_trades.append({
                "portfolio_id": portfolio_id,
                "symbol_id": symbol_id,
                "trade_type": SELL,
                "order_type": ORDER_TYPE,
                "quantity": current_quantity,
                "price": price_decimal,
                "reason": REASON
            })
        # If symbol is in allocations but current quantity > target, sell the excess
        elif symbol_id in target_quantities and current_quantity > target_quantities[symbol_id]["target_quantity"]:
            symbol_name = target_quantities[symbol_id]["symbol_name"]
            price_decimal = target_quantities[symbol_id]["price"]
            excess_quantity = current_quantity - target_quantities[symbol_id]["target_quantity"]
            
            print(f"DEBUG: Selling excess position of {symbol_name}: {float(excess_quantity)} shares at ${float(price_decimal)}")
            
            sell_trades.append({
                "portfolio_id": portfolio_id,
                "symbol_id": symbol_id,
                "trade_type": SELL,
                "order_type": ORDER_TYPE,
                "quantity": excess_quantity,
                "price": price_decimal,
                "reason": REASON
            })
    
    # Add all sell trades to the execution list
    trades_to_execute.extend(sell_trades)
    
    # Calculate total sell value
    total_sell_value = Decimal('0')
    for trade in sell_trades:
        total_sell_value += trade["price"] * trade["quantity"]
    print(f"DEBUG: Total sell value: ${float(total_sell_value):.2f}")
    
    # STEP 3: Generate buy trades for stocks that need to be increased
    buy_trades = []
    
    # For each allocation target, buy if current quantity < target quantity
    for symbol_data in target_quantities.values():
        symbol_id = symbol_data["symbol_id"]
        current_quantity = symbol_data["current_quantity"]
        target_quantity = symbol_data["target_quantity"]
        
        if current_quantity >= target_quantity:
            continue
        
        buy_quantity = target_quantity - current_quantity
        price_decimal = symbol_data["price"]
        symbol_name = symbol_data["symbol_name"]
        
        if buy_quantity < Decimal('0.0001'):
            print(f"DEBUG: Skipping {symbol_name} - buy quantity too small")
            continue
        
        buy_value = buy_quantity * price_decimal
        
        print(f"DEBUG: Buying {symbol_name}: {float(buy_quantity)} shares at ${float(price_decimal)} = ${float(buy_value):.2f}")
        
        buy_trades.append({
            "portfolio_id": portfolio_id,
            "symbol_id": symbol_id,
            "trade_type": BUY,
            "order_type": ORDER_TYPE,
            "quantity": buy_quantity,
            "price": price_decimal,
            "reason": REASON
        })
    
    # Add all buy trades to the execution list
    trades_to_execute.extend(buy_trades)
    
    # Calculate total buy value
    total_buy_value = Decimal('0')
    for trade in buy_trades:
        total_buy_value += trade["price"] * trade["quantity"]
    
    print(f"DEBUG: Total buy value: ${float(total_buy_value):.2f}")
    print(f"DEBUG: Difference (sell - buy): ${float(total_sell_value - total_buy_value):.2f}")
    print(f"DEBUG: Total trades to execute: {len(trades_to_execute)}")
    
    # Create MONEY_MARKET trade to handle any difference between sells and buys
    if total_sell_value != total_buy_value:
        difference = total_sell_value - total_buy_value
        if difference > Decimal('0'):
            # We have extra cash - buy MONEY_MARKET
            money_market_symbol = session.query(Symbol).filter(Symbol.symbol == "MONEY_MARKET").first()
            if money_market_symbol:
                print(f"DEBUG: Adding {float(difference):.2f} to MONEY_MARKET")
                buy_trades.append({
                    "portfolio_id": portfolio_id,
                    "symbol_id": money_market_symbol.symbol_id,
                    "trade_type": BUY,
                    "order_type": ORDER_TYPE,
                    "quantity": difference,  # 1:1 ratio for MONEY_MARKET
                    "price": Decimal('1'),
                    "reason": "Balance adjustment"
                })
                trades_to_execute.append(buy_trades[-1])
    
    return trades_to_execute

async def calculate_positions_value(session: Session, portfolio_id: uuid.UUID, price_date: date) -> float:
    """
    Retrieve the portfolio balance for the given date from portfolio_stats.
    
    Args:
        session (Session): The database session
        portfolio_id (UUID): The portfolio ID
        price_date (date): The date to use for retrieving portfolio balance
        
    Returns:
        float: The portfolio balance value
    """
    print(f"Getting portfolio balance for portfolio {portfolio_id} on date {price_date}")
    
    # Query the portfolio stats for the given portfolio and date (without time components)
    date_str = price_date.strftime("%Y-%m-%d")
    portfolio_stats = session.query(PortfolioStats).filter(
        PortfolioStats.portfolio_id == portfolio_id,
        func.cast(PortfolioStats.recorded_at, Date) == date_str
    ).first()
    
    if portfolio_stats:
        return float(portfolio_stats.portfolio_balance)
    else:
        print(f"No portfolio stats found for portfolio {portfolio_id} on {date_str}")
        # Try to find the most recent stats before this date
        most_recent_stats = session.query(PortfolioStats).filter(
            PortfolioStats.portfolio_id == portfolio_id,
            func.cast(PortfolioStats.recorded_at, Date) <= date_str
        ).order_by(desc(PortfolioStats.recorded_at)).first()
        
        if most_recent_stats:
            print(f"Using most recent portfolio balance from {most_recent_stats.recorded_at}: ${float(most_recent_stats.portfolio_balance):.2f}")
            return float(most_recent_stats.portfolio_balance)
        else:
            print(f"ERROR: No portfolio stats available for {portfolio_id}")
            return 0.0



async def execute_trades(session: Session, trades_to_execute: List[Dict], trade_date: str) -> List[Dict]:
    pst = pytz.timezone('America/Los_Angeles')
    # Convert the trade_date string to a datetime object at 16:00 EST (market close)
    trade_datetime = datetime.strptime(trade_date, "%Y-%m-%d")
    # Set time to 4 PM EST / 1 PM PST (typical market close time)
    trade_datetime = trade_datetime.replace(hour=13, minute=0, second=0)
    # Make it timezone aware
    trade_datetime = pst.localize(trade_datetime)
    
    executed_trades = []
    
    # First, record all trades
    trade_records = []
    for trade_data in trades_to_execute:
        # Create trade record
        new_trade = Trade(
            trade_id=uuid.uuid4(),
            portfolio_id=trade_data["portfolio_id"],
            symbol_id=trade_data["symbol_id"],
            traded_at=trade_datetime,  # Use the trade date with market close time
            trade_type=trade_data["trade_type"],
            order_type=trade_data["order_type"],
            price=trade_data["price"],
            quantity=trade_data["quantity"],
            reason=trade_data["reason"]
            # value is now a generated column and will be calculated automatically
        )
        session.add(new_trade)
        trade_records.append(new_trade)
    
    # Commit trades first to ensure they're recorded
    session.flush()
    
    # Get all current positions for this portfolio
    portfolio_id = trades_to_execute[0]["portfolio_id"]
    current_positions = {}
    
    # Query all current positions
    positions = session.query(Position).filter(
        Position.portfolio_id == portfolio_id
    ).order_by(Position.symbol_id, desc(Position.recorded_at)).all()
    
    # Get the most recent position for each symbol
    for position in positions:
        if position.symbol_id not in current_positions:
            current_positions[position.symbol_id] = position
    
    # Calculate net position changes from trades
    position_changes = {}
    for trade_data in trades_to_execute:
        symbol_id = trade_data["symbol_id"]
        quantity_change = trade_data["quantity"]
        
        if trade_data["trade_type"] == SELL:
            quantity_change = -quantity_change
            
        if symbol_id not in position_changes:
            position_changes[symbol_id] = Decimal('0')
            
        position_changes[symbol_id] += quantity_change
    
    # Create updated positions based on trades
    new_positions = []
    for symbol_id, quantity_change in position_changes.items():
        current_quantity = Decimal('0')
        
        # Get current quantity if position exists
        if symbol_id in current_positions:
            current_quantity = Decimal(str(current_positions[symbol_id].quantity))
        
        # Calculate new quantity
        new_quantity = current_quantity + quantity_change
        
        # Only create a new position record if quantity > 0
        if new_quantity > Decimal('0'):
            new_position = Position(
                position_id=uuid.uuid4(),
                portfolio_id=portfolio_id,
                symbol_id=symbol_id,
                quantity=new_quantity,
                recorded_at=trade_datetime
            )
            session.add(new_position)
            new_positions.append(new_position)
        elif symbol_id in current_positions:
            # If the position is being reduced to zero or below, log it and create a zero quantity position
            print(f"DEBUG: Position for symbol {symbol_id} is now zero or below. Closing position.")
            # Create a zero quantity position to properly record the closing
            zero_position = Position(
                position_id=uuid.uuid4(),
                portfolio_id=portfolio_id,
                symbol_id=symbol_id,
                quantity=Decimal('0'),
                recorded_at=trade_datetime
            )
            session.add(zero_position)
            new_positions.append(zero_position)
    
    # Add to executed trades list
    for trade_data in trades_to_execute:
        price = trade_data["price"]  # Already a Decimal
        quantity = trade_data["quantity"]  # Already a Decimal
        total_value = price * quantity  # Decimal * Decimal = Decimal
        
        executed_trades.append({
            "trade_id": str(trade_data.get("trade_id", uuid.uuid4())),
            "portfolio_id": str(trade_data["portfolio_id"]),
            "symbol_id": str(trade_data["symbol_id"]),
            "trade_type": trade_data["trade_type"],
            "quantity": float(quantity),
            "price": float(price),
            "total_value": float(total_value)
        })
    
    # Commit all changes
    session.commit()
    
    return executed_trades 