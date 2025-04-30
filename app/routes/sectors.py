from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..service.populate_sectors import populate_sector_tables

router = APIRouter(
    prefix="/sectors",
    tags=["sectors"],
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
def populate_sectors():
    """
    Populate the sectors and symbol_sectors tables using data from the CSV file.
    This is an admin-only endpoint that should be called only once or when refreshing sector data.
    """
    with SessionLocal() as db:
        result = populate_sector_tables(db)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result

@router.get("/")
def get_sectors(db: Session = Depends(get_db)):
    """
    Get all sectors from the database
    """
    from ..models import Sector
    
    try:
        sectors = db.query(Sector).all()
        return {
            "status": "success",
            "count": len(sectors),
            "sectors": [
                {
                    "sector_id": str(sect.sector_id),
                    "sector_name": sect.sector_name
                }
                for sect in sectors
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sectors: {str(e)}")

@router.get("/symbol/{symbol}")
def get_symbol_sectors(symbol: str, db: Session = Depends(get_db)):
    """
    Get the sectors for a specific symbol
    """
    from ..models import Symbol, SymbolSector, Sector
    
    try:
        # Get the symbol_id
        symbol_rec = db.query(Symbol).filter(Symbol.symbol == symbol.upper()).first()
        if not symbol_rec:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        
        # Get the sectors for this symbol
        results = (db.query(SymbolSector, Sector)
                  .join(Sector, SymbolSector.sector_id == Sector.sector_id)
                  .filter(SymbolSector.symbol_id == symbol_rec.symbol_id)
                  .all())
        
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "count": len(results),
            "sectors": [
                {
                    "sector_id": str(sect.Sector.sector_id),
                    "sector_name": sect.Sector.sector_name,
                    "percentage": float(sect.SymbolSector.pct)
                }
                for sect in results
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sectors for symbol {symbol}: {str(e)}") 