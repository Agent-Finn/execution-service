from ..database import SessionLocal
from datetime import datetime, timezone
from sqlalchemy import text
from decimal import Decimal

def update_portfolio_balance(portfolio_id: str, balance_change: float) -> dict:
    """
    Update the portfolio balance for a given portfolio_id.

    Args:
        portfolio_id (str): The ID of the portfolio to update
        balance_change (float): The amount to change the balance by (positive or negative)

    Returns:
        dict: The updated portfolio stats
    """
    db = SessionLocal()
    try:
        # First, get the current portfolio stats
        query = text("""
            SELECT portfolio_balance, alpha, beta, max_drawdown, sharpe_ratio, std_dev, turnover
            FROM portfolio_stats
            WHERE portfolio_id = :portfolio_id
            ORDER BY recorded_at DESC
            LIMIT 1
        """)
        
        result = db.execute(query, {"portfolio_id": portfolio_id})
        current_stats = result.fetchone()
        
        if not current_stats:
            return None

        # Calculate new balance - convert float to Decimal for compatibility
        balance_change_decimal = Decimal(str(balance_change))  # Convert via string to avoid precision issues
        new_balance = current_stats.portfolio_balance + balance_change_decimal
        
        # Insert new row with updated balance and current timestamp
        insert_query = text("""
            INSERT INTO portfolio_stats (
                portfolio_balance, recorded_at, alpha, beta, max_drawdown,
                sharpe_ratio, std_dev, turnover, portfolio_id
            )
            VALUES (
                :balance, :recorded_at, :alpha, :beta, :max_drawdown,
                :sharpe_ratio, :std_dev, :turnover, :portfolio_id
            )
            RETURNING *
        """)
        
        params = {
            "balance": new_balance,
            "recorded_at": datetime.now(timezone.utc),
            "alpha": current_stats.alpha,
            "beta": current_stats.beta,
            "max_drawdown": current_stats.max_drawdown,
            "sharpe_ratio": current_stats.sharpe_ratio,
            "std_dev": current_stats.std_dev,
            "turnover": current_stats.turnover,
            "portfolio_id": portfolio_id
        }
        
        result = db.execute(insert_query, params)
        db.commit()
        new_stats = result.fetchone()

        return {
            "portfolio_id": portfolio_id,
            "portfolio_balance": float(new_balance),  # Convert Decimal to float for JSON serialization
            "alpha": float(new_stats.alpha) if new_stats.alpha else None,
            "beta": float(new_stats.beta) if new_stats.beta else None,
            "max_drawdown": float(new_stats.max_drawdown) if new_stats.max_drawdown else None,
            "sharpe_ratio": float(new_stats.sharpe_ratio) if new_stats.sharpe_ratio else None,
            "std_dev": float(new_stats.std_dev) if new_stats.std_dev else None,
            "turnover": float(new_stats.turnover) if new_stats.turnover else None,
            "recorded_at": new_stats.recorded_at.isoformat()
        }
    finally:
        db.close() 