from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..models import PortfolioStats  # Import the PortfolioStats model
from ..database import SessionLocal  # Import SessionLocal for sync ORM
from uuid import UUID

def get_portfolio_stats_by_portfolio(portfolio_id: UUID):
    """
    Fetch all portfolio stats for a given portfolio_id.
    
    Args:
        portfolio_id (UUID): The portfolio ID to filter stats.
    
    Returns:
        dict: A list of portfolio stats in the format {"portfolio_stats": [...]}.
    
    Raises:
        HTTPException: 404 if no stats are found, 500 for other errors.
    """
    try:
        with SessionLocal() as session:
            # Query portfolio stats for the given portfolio_id
            stats = session.query(PortfolioStats).filter(PortfolioStats.portfolio_id == portfolio_id).all()
            
            if not stats:
                raise HTTPException(status_code=404, detail=f"No stats found for portfolio_id {portfolio_id}")
            
            # Convert to dicts for response
            stats_list = [
                {
                    "stat_id": stat.stat_id,
                    "portfolio_id": stat.portfolio_id,
                    "portfolio_balance": float(stat.portfolio_balance) if stat.portfolio_balance is not None else None,
                    "recorded_at": stat.recorded_at.isoformat() if stat.recorded_at else None,
                    "alpha": float(stat.alpha) if stat.alpha is not None else None,
                    "beta": float(stat.beta) if stat.beta is not None else None,
                    "max_drawdown": float(stat.max_drawdown) if stat.max_drawdown is not None else None,
                    "sharpe_ratio": float(stat.sharpe_ratio) if stat.sharpe_ratio is not None else None,
                    "std_dev": float(stat.std_dev) if stat.std_dev is not None else None,
                    "turnover": float(stat.turnover) if stat.turnover is not None else None
                }
                for stat in stats
            ]
            return {"portfolio_stats": stats_list}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Failed to fetch portfolio stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch portfolio stats: {str(e)}")