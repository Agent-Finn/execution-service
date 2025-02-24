from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..models import Position  # Import the Position model
from ..database import SessionLocal  # Import SessionLocal for sync ORM

def get_positions_by_portfolio(portfolio_id: int):
    """
    Fetch all positions for a given portfolio_id.
    
    Args:
        portfolio_id (int): The portfolio ID to filter positions.
    
    Returns:
        dict: A list of positions in the format {"positions": [...]}.
    
    Raises:
        HTTPException: 404 if no positions are found, 500 for other errors.
    """
    try:
        with SessionLocal() as session:
            # Query positions for the given portfolio_id
            positions = session.query(Position).filter(Position.portfolio_id == portfolio_id).all()
            
            if not positions:
                raise HTTPException(status_code=404, detail=f"No positions found for portfolio_id {portfolio_id}")
            
            # Convert to dicts for response
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
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Failed to fetch positions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")