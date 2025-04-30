import uuid
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models import Allocation, SymbolSector, PortfolioSectorStats
from ..database import SessionLocal

def calculate_sector_allocations(batch_id: uuid.UUID):
    """
    Calculate sector allocations for a given batch ID, print intermediate and final results for debugging,
    and do not write to the database.
    
    Args:
        batch_id (uuid.UUID): The ID of the allocation batch to process.
    """
    with SessionLocal() as session:
        # Query to get intermediate contributions
        intermediate_query = session.query(
            Allocation.symbol_id,
            SymbolSector.sector_id,
            Allocation.allocation_pct,
            SymbolSector.pct,
            (Allocation.allocation_pct * SymbolSector.pct).label('contribution')
        ).join(
            SymbolSector, Allocation.symbol_id == SymbolSector.symbol_id
        ).filter(
            Allocation.allocation_batch_id == batch_id
        ).all()

        # Print intermediate results
        print("Intermediate Contributions:")
        for row in intermediate_query:
            print(f"Symbol ID: {row.symbol_id}, Sector ID: {row.sector_id}, "
                  f"Allocation Pct: {row.allocation_pct:.4f}, Sector Pct: {row.pct:.4f}, "
                  f"Contribution: {row.contribution:.4f}")

        # Calculate total allocation per sector
        sector_allocations = session.query(
            SymbolSector.sector_id,
            func.sum(Allocation.allocation_pct * SymbolSector.pct).label('sector_pct')
        ).join(
            SymbolSector, Allocation.symbol_id == SymbolSector.symbol_id
        ).filter(
            Allocation.allocation_batch_id == batch_id
        ).group_by(
            SymbolSector.sector_id
        ).all()

        # Print final results
        print("\nFinal Sector Allocations:")
        for sector_id, sector_pct in sector_allocations:
            print(f"Sector ID: {sector_id}, Total Allocation: {sector_pct:.4f}")

        # Database write operations (commented out to prevent writing)
        if sector_allocations:
            stat_id = uuid.uuid4()
            for sector_id, sector_pct in sector_allocations:
                new_stat = PortfolioSectorStats(
                    stat_id=stat_id,
                    sector_id=sector_id,
                    pct=sector_pct
                )
                session.add(new_stat)
            # session.commit()  # Commented out to avoid writing to the database
        else:
            print(f"No sector allocations to insert for batch_id: {batch_id}")