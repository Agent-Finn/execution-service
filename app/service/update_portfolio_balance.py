import uuid
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import quantstats as qs
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from ..database import SessionLocal
from ..models import Symbol, Position, PortfolioStats, SymbolPrice, Trade
from .utils import get_symbol_id, get_symbol_price

def is_trading_day(day: date) -> bool:
    """
    Check if a given date is a trading day (not weekend).
    
    Args:
        day (date): The date to check
        
    Returns:
        bool: True if it's a trading day, False otherwise
    """
    # Check if the day is a weekend (5 = Saturday, 6 = Sunday)
    if day.weekday() >= 5:
        return False
    
    # Future enhancement: Check for holidays
    return True

def get_all_days_in_month(year: int, month: int) -> List[date]:
    """
    Get all days in a given month.
    
    Args:
        year (int): The year
        month (int): The month (1-12)
        
    Returns:
        List[date]: List of all dates in the month
    """
    # Create a range of all days in the month
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    
    current_month = date(year, month, 1)
    days = []
    
    # Iterate through all days of the month
    current_day = current_month
    while current_day < next_month:
        days.append(current_day)
        current_day += timedelta(days=1)
    
    return days

def get_trading_days_in_month(year: int, month: int) -> List[date]:
    """
    Get all trading days in a given month.
    
    Args:
        year (int): The year
        month (int): The month (1-12)
        
    Returns:
        List[date]: List of dates that are trading days in the month
    """
    all_days = get_all_days_in_month(year, month)
    return [day for day in all_days if is_trading_day(day)]

def calculate_portfolio_metrics(session: Session, portfolio_id: uuid.UUID, end_date: date, days_lookback: int = 90) -> Dict[str, Decimal]:
    """
    Calculate portfolio performance metrics including alpha and beta.
    
    Args:
        session (Session): Database session
        portfolio_id (uuid.UUID): Portfolio ID
        end_date (date): End date for calculations
        days_lookback (int): Number of days to look back for calculations
        
    Returns:
        Dict[str, Decimal]: Dictionary of calculated metrics
    """
    start_date = end_date - timedelta(days=days_lookback)
    start_datetime = datetime.combine(start_date, datetime.min.time())
    # Use < next‑day midnight so we include every row that falls on end_date,
    # regardless of its timestamp.
    end_datetime = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
    
    # Get portfolio balance history
    portfolio_stats = session.query(PortfolioStats).filter(
        PortfolioStats.portfolio_id == portfolio_id,
        PortfolioStats.recorded_at >= start_datetime,
        PortfolioStats.recorded_at < end_datetime
    ).order_by(PortfolioStats.recorded_at).all()
    
    if len(portfolio_stats) < 2:
        # Not enough data points for calculations
        return {
            "alpha": Decimal('0'),
            "beta": Decimal('0'),
            "sharpe_ratio": Decimal('0'),
            "max_drawdown": Decimal('0'),
            "std_dev": Decimal('0')
        }
    
    # Convert portfolio balance history to pandas series for quantstats
    dates = [
        stat.recorded_at.replace(tzinfo=None)
        if isinstance(stat.recorded_at, datetime) and stat.recorded_at.tzinfo
        else stat.recorded_at
        for stat in portfolio_stats
    ]
    values = [float(stat.portfolio_balance) for stat in portfolio_stats]
    portfolio_series = pd.Series(values, index=dates)
    
    # Calculate daily returns
    portfolio_returns = portfolio_series.pct_change().dropna()
    portfolio_returns = portfolio_returns.replace([np.inf, -np.inf], np.nan).dropna()
    
    # Get benchmark data (e.g., S&P 500)
    # You'll need to have S&P 500 or another benchmark in your database
    # For now, let's try to get a market benchmark from your database
    benchmark_symbol_id = get_symbol_id(session, "SPY")  # Assuming SPY is your benchmark
    if not benchmark_symbol_id:
        # Fallback metrics if no benchmark is available
        return {
            "alpha": Decimal('0'),
            "beta": Decimal('0'),
            "sharpe_ratio": Decimal(str(qs.stats.sharpe(portfolio_returns))),
            "max_drawdown": Decimal(str(qs.stats.max_drawdown(portfolio_returns))),
            "std_dev": Decimal(str(portfolio_returns.std()))
        }
    
    # Get benchmark prices
    benchmark_prices = session.query(
        SymbolPrice.price_at,
        SymbolPrice.price
    ).filter(
        SymbolPrice.symbol_id == benchmark_symbol_id,
        SymbolPrice.price_at >= start_datetime,
        SymbolPrice.price_at < end_datetime
    ).order_by(SymbolPrice.price_at).all()
    
    if not benchmark_prices:
        # No benchmark data available
        return {
            "alpha": Decimal('0'),
            "beta": Decimal('0'),
            "sharpe_ratio": Decimal(str(qs.stats.sharpe(portfolio_returns))),
            "max_drawdown": Decimal(str(qs.stats.max_drawdown(portfolio_returns))),
            "std_dev": Decimal(str(portfolio_returns.std()))
        }
    
    # Convert benchmark prices to pandas series
    benchmark_dates = [
        price.price_at.replace(tzinfo=None)
        if isinstance(price.price_at, datetime) and price.price_at.tzinfo
        else price.price_at
        for price in benchmark_prices
    ]
    benchmark_values = [float(price.price) for price in benchmark_prices]
    benchmark_series = pd.Series(benchmark_values, index=benchmark_dates)
    
    # Calculate benchmark returns
    benchmark_returns = benchmark_series.pct_change().dropna()
    benchmark_returns = benchmark_returns.replace([np.inf, -np.inf], np.nan).dropna()
    
    # Align portfolio and benchmark returns
    portfolio_returns, benchmark_returns = portfolio_returns.align(benchmark_returns, join='inner')
    
    if len(portfolio_returns) < 2:
        # Not enough aligned data points
        return {
            "alpha": Decimal('0'),
            "beta": Decimal('0'),
            "sharpe_ratio": Decimal('0'),
            "max_drawdown": Decimal('0'),
            "std_dev": Decimal('0')
        }
    
    # Calculate metrics using quantstats
    try:
        # Check if we have enough valid data for calculations
        if len(portfolio_returns) < 2 or portfolio_returns.isna().any() or benchmark_returns.isna().any():
            return {
                "alpha": Decimal('0'),
                "beta": Decimal('0'),
                "sharpe_ratio": Decimal('0'),
                "max_drawdown": Decimal('0'),
                "std_dev": Decimal('0')
            }
            
        # Replace any inf values
        portfolio_returns = portfolio_returns.replace([np.inf, -np.inf], np.nan).dropna()
        benchmark_returns = benchmark_returns.replace([np.inf, -np.inf], np.nan).dropna()
        
        # Check if we still have enough data after cleaning
        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
            return {
                "alpha": Decimal('0'),
                "beta": Decimal('0'),
                "sharpe_ratio": Decimal('0'),
                "max_drawdown": Decimal('0'),
                "std_dev": Decimal('0')
            }
            
        # Align the series to make sure they have matching dates
        portfolio_returns, benchmark_returns = portfolio_returns.align(benchmark_returns, join='inner')
        
        # Calculate metrics safely
        try:
            greek_metrics = qs.stats.greeks(portfolio_returns, benchmark_returns)
            alpha = greek_metrics.get('alpha', 0)
            beta = greek_metrics.get('beta', 0)
        except Exception as e:
            print(f"Error calculating alpha/beta: {str(e)}")
            alpha, beta = 0, 0
            
        try:
            sharpe = qs.stats.sharpe(portfolio_returns)
        except Exception as e:
            print(f"Error calculating sharpe: {str(e)}")
            sharpe = 0
            
        try:
            max_dd = qs.stats.max_drawdown(portfolio_returns)
        except Exception as e:
            print(f"Error calculating max_drawdown: {str(e)}")
            max_dd = 0
            
        try:
            std_dev = portfolio_returns.std() if len(portfolio_returns) > 1 else 0
        except Exception as e:
            print(f"Error calculating std_dev: {str(e)}")
            std_dev = 0
        
        # Sanitize values to avoid NaN/inf
        for _name, _val in [("alpha", alpha), ("beta", beta), ("sharpe", sharpe),
                            ("max_dd", max_dd), ("std_dev", std_dev)]:
            if _val is None or np.isnan(_val) or np.isinf(_val):
                locals()[_name] = 0.0
        
        # Round alpha and beta to three decimal places
        alpha = round(float(alpha), 3)
        beta = round(float(beta), 3)
        
        return {
            "alpha": Decimal(str(alpha)),
            "beta": Decimal(str(beta)),
            "sharpe_ratio": Decimal(str(float(sharpe))),
            "max_drawdown": Decimal(str(float(max_dd))),
            "std_dev": Decimal(str(float(std_dev)))
        }
    except Exception as e:
        print(f"Error calculating portfolio metrics: {str(e)}")
        return {
            "alpha": Decimal('0'),
            "beta": Decimal('0'),
            "sharpe_ratio": Decimal('0'),
            "max_drawdown": Decimal('0'),
            "std_dev": Decimal('0')
        }

def calculate_portfolio_turnover(session: Session, portfolio_id: uuid.UUID, end_date: date, lookback_days: int = 60) -> Decimal:
    """
    Calculate portfolio turnover - the rate at which assets are bought and sold.
    Uses the trades table for actual trade data.
    
    Args:
        session (Session): Database session
        portfolio_id (uuid.UUID): Portfolio ID
        end_date (date): End date for calculations
        lookback_days (int): Number of days to look back for turnover calculation (extended to 60 days to capture monthly trades)
        
    Returns:
        Decimal: Portfolio turnover as a decimal (e.g., 0.25 = 25% turnover)
    """
    try:
        # Calculate the start date for lookback period
        start_date = end_date - timedelta(days=lookback_days)
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        print(f"Calculating turnover for portfolio {portfolio_id} from {start_date} to {end_date}")
        
        # Get trades from the trades table
        trades = session.query(Trade).filter(
            Trade.portfolio_id == portfolio_id,
            Trade.traded_at >= start_datetime,
            Trade.traded_at <= end_datetime
        ).order_by(Trade.traded_at).all()
        
        print(f"Found {len(trades)} trades in the period")
        
        if not trades:
            return Decimal('0')
        
        # Calculate total value of buys and sells from actual trades
        total_buys = Decimal('0')
        total_sells = Decimal('0')
        
        for trade in trades:
            try:
                # Use the value field if it exists and is not None, otherwise calculate price * quantity
                if hasattr(trade, 'value') and trade.value is not None:
                    trade_value = abs(Decimal(str(trade.value)))
                    value_source = "value field"
                else:
                    trade_value = abs(Decimal(str(trade.price)) * Decimal(str(trade.quantity)))
                    value_source = "price * quantity"
                
                # Determine if buy or sell based on trade_type field
                if trade.trade_type == "Buy":
                    total_buys += trade_value
                    print(f"Buy trade on {trade.traded_at.date()}: ${float(trade_value):.2f} ({value_source})")
                elif trade.trade_type == "Sell":
                    total_sells += trade_value
                    print(f"Sell trade on {trade.traded_at.date()}: ${float(trade_value):.2f} ({value_source})")
            except Exception as e:
                print(f"Error processing trade {trade.trade_id}: {str(e)}")
                continue
        
        print(f"Total buys: ${float(total_buys):.2f}, Total sells: ${float(total_sells):.2f}")
        
        # Get average portfolio value during the period
        portfolio_stats = session.query(PortfolioStats).filter(
            PortfolioStats.portfolio_id == portfolio_id,
            PortfolioStats.recorded_at >= start_datetime,
            PortfolioStats.recorded_at <= end_datetime
        ).all()
        
        if not portfolio_stats:
            # If no portfolio stats are available, estimate from current positions
            latest_positions = session.query(Position).filter(
                Position.portfolio_id == portfolio_id,
                Position.recorded_at <= end_datetime
            ).order_by(Position.symbol_id, desc(Position.recorded_at)).all()
            
            # Group by symbol to get latest position for each symbol
            latest_by_symbol = {}
            for pos in latest_positions:
                if pos.symbol_id not in latest_by_symbol:
                    latest_by_symbol[pos.symbol_id] = pos
            
            # Calculate total value
            total_value = Decimal('0')
            for pos in latest_by_symbol.values():
                price = get_symbol_price(session, pos.symbol_id, end_date)
                if price:
                    total_value += Decimal(str(pos.quantity)) * Decimal(str(price))
            
            average_value = total_value
            print(f"No portfolio stats found. Estimated value: ${float(average_value):.2f}")
        else:
            # Calculate average portfolio value from stats
            total_value = sum(Decimal(str(stat.portfolio_balance)) for stat in portfolio_stats)
            average_value = total_value / len(portfolio_stats) if portfolio_stats else Decimal('0')
            print(f"Average portfolio value from {len(portfolio_stats)} stats: ${float(average_value):.2f}")
        
        # Avoid division by zero
        if average_value == 0:
            print("Average portfolio value is zero, returning 0 turnover")
            return Decimal('0')
        
        # Use max of buys and sells to account for one-sided activity
        turnover = max(total_buys, total_sells) / average_value
        print(f"Raw turnover (using max of buys/sells): {float(turnover):.8f}")
        
        # Annualize the turnover (multiply by 365/lookback_days)
        annualized_factor = Decimal('365') / Decimal(str(lookback_days))
        annualized_turnover = turnover * annualized_factor
        print(f"Annualized turnover: {float(annualized_turnover):.8f}")
        
        # Don't cap at 1.0 to show full turnover value
        # Use higher precision (8 decimal places)
        result = annualized_turnover.quantize(Decimal('0.00000001'))
        print(f"Final turnover value: {float(result):.8f}")
        return result
        
    except Exception as e:
        print(f"Error calculating portfolio turnover: {str(e)}")
        import traceback
        traceback.print_exc()
        return Decimal('0')

def update_portfolio_balance_for_day(session: Session, portfolio_id: uuid.UUID, trading_day: date, last_known_balance: Optional[Decimal] = None, last_known_alpha: Optional[Decimal] = None, last_known_beta: Optional[Decimal] = None, last_known_max_drawdown: Optional[Decimal] = None, last_known_std_dev: Optional[Decimal] = None, last_known_turnover: Optional[Decimal] = None) -> Tuple[Optional[Dict], Optional[Decimal], Optional[Decimal], Optional[Decimal], Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
    """
    Update portfolio balance for a specific day.
    
    Args:
        session (Session): Database session
        portfolio_id (uuid.UUID): Portfolio ID
        trading_day (date): Day to update
        last_known_balance (Optional[Decimal]): Last known portfolio balance
        last_known_alpha (Optional[Decimal]): Last known alpha value
        last_known_beta (Optional[Decimal]): Last known beta value
        last_known_max_drawdown (Optional[Decimal]): Last known max drawdown value
        last_known_std_dev (Optional[Decimal]): Last known standard deviation value
        last_known_turnover (Optional[Decimal]): Last known turnover value
        
    Returns:
        Tuple[Optional[Dict], Optional[Decimal], Optional[Decimal], Optional[Decimal], Optional[Decimal], Optional[Decimal], Optional[Decimal]]: 
            (Updated portfolio stats or None if error, last known balance, last known alpha, last known beta, last known max drawdown, last known std dev, last known turnover)
    """
    try:
        # If it's not a trading day and we have a last known balance, use it
        if not is_trading_day(trading_day) and last_known_balance is not None:
            # Use last known values for alpha and beta, defaulting to 0 if not available
            alpha_value = last_known_alpha if last_known_alpha is not None else Decimal('0')
            beta_value = last_known_beta if last_known_beta is not None else Decimal('0')
            max_drawdown_value = last_known_max_drawdown if last_known_max_drawdown is not None else Decimal('0')
            std_dev_value = last_known_std_dev if last_known_std_dev is not None else Decimal('0')
            turnover_value = last_known_turnover if last_known_turnover is not None else Decimal('0')
            
            # Create a new portfolio stats entry with the last known balance and metrics
            new_stats = PortfolioStats(
                stat_id=uuid.uuid4(),
                portfolio_id=portfolio_id,
                portfolio_balance=last_known_balance,
                recorded_at=datetime.combine(trading_day, datetime.min.time()),
                alpha=alpha_value,
                beta=beta_value,
                max_drawdown=max_drawdown_value,
                sharpe_ratio=Decimal('0'),
                std_dev=std_dev_value,
                turnover=turnover_value
            )
            
            session.add(new_stats)
            session.commit()
            
            return {
                "stat_id": str(new_stats.stat_id),
                "portfolio_id": str(portfolio_id),
                "portfolio_balance": float(last_known_balance),
                "recorded_at": new_stats.recorded_at.isoformat(),
                "trading_day": trading_day.isoformat(),
                "is_trading_day": False,
                "alpha": float(alpha_value),
                "beta": float(beta_value),
                "max_drawdown": float(max_drawdown_value),
                "std_dev": float(std_dev_value),
                "turnover": float(turnover_value)
            }, last_known_balance, alpha_value, beta_value, max_drawdown_value, std_dev_value, turnover_value
        
        # Get the latest position for each symbol in the portfolio
        latest_positions = {}
        
        # Find all symbol_ids that have positions for this portfolio
        symbol_ids = session.query(Position.symbol_id).filter(
            Position.portfolio_id == portfolio_id,
            Position.recorded_at <= trading_day
        ).distinct().all()
        
        # For each symbol_id, get the latest position before the trading day
        for (symbol_id,) in symbol_ids:
            latest_position = session.query(Position).filter(
                Position.portfolio_id == portfolio_id,
                Position.symbol_id == symbol_id,
                Position.recorded_at <= trading_day
            ).order_by(desc(Position.recorded_at)).first()
            
            if latest_position:
                latest_positions[symbol_id] = latest_position
        
        if not latest_positions:
            print(f"No positions found for portfolio {portfolio_id} for month of {trading_day}")
            return None, last_known_balance, last_known_alpha, last_known_beta, last_known_max_drawdown, last_known_std_dev, last_known_turnover
        
        # Calculate total portfolio value based on the latest positions and prices
        total_value = Decimal('0')
        
        for position in latest_positions.values():
            # Get price for this trading day
            price = get_symbol_price(session, position.symbol_id, trading_day)
            if price is None:
                print(f"Warning: missing price for symbol {position.symbol_id} on {trading_day}")
                continue
            position_value = Decimal(str(price)) * Decimal(str(position.quantity))
            total_value += position_value
        
        print(f"Portfolio value for {trading_day}: ${float(total_value)}")
        
        # Calculate portfolio metrics
        metrics = calculate_portfolio_metrics(session, portfolio_id, trading_day)
        
        # Calculate turnover
        # For this implementation, we'll look at position changes in the last 30 days
        # A more sophisticated approach would be part of a separate function
        turnover = calculate_portfolio_turnover(session, portfolio_id, trading_day)
        
        # Create a new portfolio stats entry
        new_stats = PortfolioStats(
            stat_id=uuid.uuid4(),
            portfolio_id=portfolio_id,
            portfolio_balance=total_value,
            recorded_at=datetime.combine(trading_day, datetime.min.time()),
            alpha=metrics["alpha"],
            beta=metrics["beta"],
            max_drawdown=metrics["max_drawdown"],
            sharpe_ratio=metrics["sharpe_ratio"],
            std_dev=metrics["std_dev"],
            turnover=turnover
        )
        
        session.add(new_stats)
        session.commit()
        
        return {
            "stat_id": str(new_stats.stat_id),
            "portfolio_id": str(portfolio_id),
            "portfolio_balance": float(total_value),
            "recorded_at": new_stats.recorded_at.isoformat(),
            "trading_day": trading_day.isoformat(),
            "is_trading_day": True,
            "alpha": float(metrics["alpha"]),
            "beta": float(metrics["beta"]),
            "max_drawdown": float(metrics["max_drawdown"]),
            "std_dev": float(metrics["std_dev"]),
            "turnover": float(turnover)
        }, total_value, metrics["alpha"], metrics["beta"], metrics["max_drawdown"], metrics["std_dev"], turnover
    
    except Exception as e:
        session.rollback()
        print(f"Error updating portfolio balance for {trading_day}: {str(e)}")
        return None, last_known_balance, last_known_alpha, last_known_beta, last_known_max_drawdown, last_known_std_dev, last_known_turnover

def update_portfolio_balance(portfolio_id_str: str, year: int, month: int) -> Dict:
    """
    Update portfolio balances for all days in a given month.
    
    Args:
        portfolio_id_str (str): Portfolio ID as string
        year (int): Year of the month to update
        month (int): Month to update (1-12)
        
    Returns:
        Dict: Results of the update operation
    """
    try:
        portfolio_id = uuid.UUID(portfolio_id_str)
        
        # Get all days in the month
        all_days = get_all_days_in_month(year, month)
        
        if not all_days:
            return {
                "status": "error",
                "message": f"No days found in month {month}/{year}"
            }
        
        results = []
        errors = []
        last_known_balance = None
        last_known_alpha = None
        last_known_beta = None
        last_known_max_drawdown = None
        last_known_std_dev = None
        last_known_turnover = None
        
        with SessionLocal() as session:
            # Check if there's a previous balance from before this month
            previous_stat = session.query(PortfolioStats).filter(
                PortfolioStats.portfolio_id == portfolio_id,
                PortfolioStats.recorded_at < datetime.combine(all_days[0], datetime.min.time())
            ).order_by(desc(PortfolioStats.recorded_at)).first()
            
            if previous_stat:
                last_known_balance = previous_stat.portfolio_balance
                last_known_alpha = previous_stat.alpha
                last_known_beta = previous_stat.beta
                last_known_max_drawdown = previous_stat.max_drawdown
                last_known_std_dev = previous_stat.std_dev
                last_known_turnover = previous_stat.turnover
            
            # Update portfolio balance for each day
            for day in all_days:
                result, last_known_balance, last_known_alpha, last_known_beta, last_known_max_drawdown, last_known_std_dev, last_known_turnover = update_portfolio_balance_for_day(
                    session, portfolio_id, day, last_known_balance, last_known_alpha, last_known_beta, last_known_max_drawdown, last_known_std_dev, last_known_turnover
                )
                if result:
                    results.append(result)
                else:
                    errors.append(day.isoformat())
        
        return {
            "status": "success",
            "message": f"Updated portfolio balance for {len(results)} days in {month}/{year}",
            "days_updated": len(results),
            "total_days": len(all_days),
            "errors": errors,
            "updates": results
        }
    
    except Exception as e:
        print(f"Error in update_portfolio_balance: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to update portfolio balance: {str(e)}"
        }
