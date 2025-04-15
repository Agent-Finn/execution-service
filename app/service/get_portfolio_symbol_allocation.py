from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Position, Symbol, SymbolSector, Sector, PortfolioSectorStats, PortfolioStats
from typing import Dict, List
from uuid import UUID
from fastapi import HTTPException
from decimal import Decimal

def get_portfolio_symbol_allocation(portfolio_id: UUID) -> Dict:
    """
    Calculate symbol allocations and sector distributions for a portfolio.
    
    Args:
        portfolio_id (UUID): The ID of the portfolio to analyze
        
    Returns:
        Dict: A dictionary containing:
            - portfolio_id: The portfolio ID
            - existing_sector_allocations: Dict mapping sectors to their current allocations in the database
            - allocations: Dict mapping symbols to their portfolio allocation percentages
            - total_quantity: Total quantity of shares in the portfolio
            - symbol_sectors: Dict mapping symbols to their sector distributions
            - sector_allocations: Dict mapping sectors to their calculated portfolio allocation percentages
            - total_value: Total portfolio value
        
    Raises:
        HTTPException: If there's an error processing the request or no positions found
    """
    try:
        with SessionLocal() as session:
            # First, get existing portfolio sector allocations
            existing_sector_allocations = {}
            
            # Find the most recent portfolio stats record
            portfolio_stats = session.query(PortfolioStats).filter(
                PortfolioStats.portfolio_id == portfolio_id
            ).order_by(PortfolioStats.recorded_at.desc()).first()
            
            if portfolio_stats:
                # Query sector allocations for this stats record
                sector_stats = (
                    session.query(PortfolioSectorStats, Sector)
                    .join(Sector, PortfolioSectorStats.sector_id == Sector.sector_id)
                    .filter(PortfolioSectorStats.stat_id == portfolio_stats.stat_id)
                    .all()
                )
                
                # Create dictionary of sector name to allocation percentage
                for stat, sector in sector_stats:
                    existing_sector_allocations[sector.sector_name] = float(stat.pct)
            
            # Query all positions and symbols for the given portfolio
            positions = (
                session.query(Position, Symbol)
                .join(Symbol, Position.symbol_id == Symbol.symbol_id)
                .filter(Position.portfolio_id == portfolio_id)
                .all()
            )
            
            if not positions:
                raise HTTPException(
                    status_code=404,
                    detail=f"No positions found for portfolio_id {portfolio_id}"
                )
            
            # Calculate total quantity and gather symbol_ids
            total_quantity = sum(position.quantity for position, _ in positions)
            
            if total_quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid total quantity - portfolio appears to have no holdings"
                )
            
            # Calculate allocation percentages and gather symbol_ids
            allocations = {}
            symbol_sectors = {}
            symbol_ids = []
            position_values = {}  # Store position values for sector calculations
            total_value = Decimal('0')
            
            # Calculate position values and quantity-based allocations
            for position, symbol in positions:
                # Calculate position value
                position_value = Decimal(str(position.quantity)) * Decimal(str(symbol.price))
                position_values[symbol.symbol_id] = position_value
                total_value += position_value
                
                # Calculate quantity-based allocation
                allocation_pct = (position.quantity / total_quantity) * 100
                allocations[symbol.symbol] = float(allocation_pct)
                symbol_ids.append(symbol.symbol_id)
            
            # Query sector distributions for all symbols in the portfolio
            sector_distributions = (
                session.query(SymbolSector, Sector)
                .join(Sector, SymbolSector.sector_id == Sector.sector_id)
                .filter(SymbolSector.symbol_id.in_(symbol_ids))
                .all()
            )
            
            # Group sector distributions by symbol_id for validation
            symbol_sector_data = {}
            for symbol_sector, sector in sector_distributions:
                symbol_id = symbol_sector.symbol_id
                if symbol_id not in symbol_sector_data:
                    symbol_sector_data[symbol_id] = []
                
                symbol_sector_data[symbol_id].append({
                    'sector_name': sector.sector_name,
                    'sector_id': sector.sector_id,
                    'pct': Decimal(str(symbol_sector.pct))
                })
            
            # Validate and normalize sector percentages
            for symbol_id, sectors in symbol_sector_data.items():
                total_pct = sum(s['pct'] for s in sectors)
                
                # Log warning if percentages don't add up to 100
                if abs(total_pct - Decimal('100')) > Decimal('0.01'):
                    print(f"Warning: Sector percentages for symbol_id {symbol_id} sum to {total_pct}, not 100")
                    
                    # Normalize to ensure they add up to 100%
                    if total_pct > Decimal('0'):
                        for sector in sectors:
                            sector['pct'] = (sector['pct'] / total_pct) * Decimal('100')
            
            # Initialize sector allocations
            sector_allocations = {}
            
            # Organize sector distributions by symbol and calculate sector allocations
            for symbol_id, sectors in symbol_sector_data.items():
                # Find the symbol for this symbol_id
                for position, symbol in positions:
                    if symbol.symbol_id == symbol_id:
                        # Get position value
                        position_value = position_values[symbol_id]
                        
                        # Initialize symbol sectors dict if needed
                        if symbol.symbol not in symbol_sectors:
                            symbol_sectors[symbol.symbol] = {}
                        
                        # Add sectors and calculate sector allocation
                        for sector_data in sectors:
                            sector_name = sector_data['sector_name']
                            sector_pct = sector_data['pct']
                            
                            # Add to symbol_sectors
                            symbol_sectors[symbol.symbol][sector_name] = float(sector_pct)
                            
                            # Calculate sector value
                            sector_value = position_value * sector_pct / Decimal('100')
                            
                            if sector_name not in sector_allocations:
                                sector_allocations[sector_name] = Decimal('0')
                            sector_allocations[sector_name] += sector_value
            
            # Convert sector allocations to percentages
            sector_allocations = {
                sector: float(value * Decimal('100') / total_value) if total_value > 0 else 0
                for sector, value in sector_allocations.items()
            }
            
            return {
                "portfolio_id": str(portfolio_id),
                "existing_sector_allocations": existing_sector_allocations,
                "allocations": allocations,
                "total_quantity": total_quantity,
                "symbol_sectors": symbol_sectors,
                "sector_allocations": sector_allocations,
                "total_value": float(total_value)
            }
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating portfolio allocations: {str(e)}"
        ) 