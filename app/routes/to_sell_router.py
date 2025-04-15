from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..sell_logic import ExecutionService
from ..database import SessionLocal
from uuid import UUID


######### 
# DEPRECATED

router = APIRouter(
    prefix="/execution",
    tags=["deprecated"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create service instance
execution_service = ExecutionService()

@router.get("/portfolio/{portfolio_id}/stocks-to-sell")
def get_stocks_to_sell(portfolio_id: int, db: Session = Depends(get_db)):
    """
    Determine which stocks in a portfolio should be sold based on current allocations.
    """
    try:
        stocks_to_sell = execution_service.determine_stocks_to_sell(db, portfolio_id)
        return {"stocks_to_sell": stocks_to_sell}
    except HTTPException as he:
        raise he

@router.post("/portfolio/{portfolio_id}/execute-sells")
def execute_sells(portfolio_id: UUID, db: Session = Depends(get_db)):
    """
    Execute sell orders for stocks not in current allocations.
    """
    try:
        result = execution_service.execute_sell_orders(db, portfolio_id)
        return result
    except HTTPException as he:
        raise he