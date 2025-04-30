from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..service.populate_industries import populate_industry_tables

router = APIRouter(
    prefix="/industries",
    tags=["industries"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/populate")
def populate_industries():
    """
    Populate the industries and symbol_industries tables using data from the CSV file.
    This is an admin-only endpoint that should be called only once or when refreshing industry data.
    """
    with SessionLocal() as db:
        result = populate_industry_tables(db)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result

@router.get("/")
def get_industries(db: Session = Depends(get_db)):
    """
    Get all industries from the database
    """
    from ..models import Industry
    
    try:
        industries = db.query(Industry).all()
        return {
            "status": "success",
            "count": len(industries),
            "industries": [
                {
                    "industry_id": str(ind.industry_id),
                    "industry": ind.industry,
                    "last_updated_at": ind.last_updated_at.isoformat() if ind.last_updated_at else None
                }
                for ind in industries
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch industries: {str(e)}")

@router.get("/symbol/{symbol}")
def get_symbol_industries(symbol: str, db: Session = Depends(get_db)):
    """
    Get the industries for a specific symbol
    """
    from ..models import Symbol, SymbolIndustry, Industry
    
    try:
        # Get the symbol_id
        symbol_rec = db.query(Symbol).filter(Symbol.symbol == symbol.upper()).first()
        if not symbol_rec:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        
        # Get the industries for this symbol
        results = (db.query(SymbolIndustry, Industry)
                  .join(Industry, SymbolIndustry.industry_id == Industry.industry_id)
                  .filter(SymbolIndustry.symbol_id == symbol_rec.symbol_id)
                  .all())
        
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "count": len(results),
            "industries": [
                {
                    "industry_id": str(ind.Industry.industry_id),
                    "industry": ind.Industry.industry,
                    "percentage": float(ind.SymbolIndustry.pct)
                }
                for ind in results
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch industries for symbol {symbol}: {str(e)}") 