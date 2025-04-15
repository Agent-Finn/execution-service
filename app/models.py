from sqlalchemy import Column, Integer, String, DateTime, Numeric, func, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
# SQLAlchemy Base
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=False)
    clerk_id = Column(String, nullable=False)

class Allocation(Base):
    __tablename__ = "allocations"
    allocated_at = Column(DateTime(timezone=True))
    allocation_pct = Column(Numeric)
    allocation_id = Column(UUID(as_uuid=True), primary_key=True)
    portfolio_id = Column(UUID(as_uuid=True))
    symbol_id = Column(UUID(as_uuid=True))
    allocation_batch_id = Column(UUID(as_uuid=True))

class PortfolioSectorStats(Base):
    __tablename__ = "portfolio_sector_stats"
    stat_id = Column(UUID(as_uuid=True), nullable=False)
    sector_id = Column(UUID(as_uuid=True), nullable=False)
    pct = Column(Numeric, nullable=False)
    
    # Add composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('stat_id', 'sector_id'),
    )

class Position(Base):
    __tablename__ = "positions"
    position_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    portfolio_id = Column(UUID(as_uuid=True), nullable=False)
    symbol_id = Column(UUID(as_uuid=True), nullable=False)
    quantity = Column(Integer, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)

class PortfolioStats(Base):
    __tablename__ = "portfolio_stats"
    stat_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    portfolio_id = Column(UUID(as_uuid=True), nullable=False)
    portfolio_balance = Column(Numeric, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    alpha = Column(Numeric, nullable=False)
    beta = Column(Numeric, nullable=False)
    max_drawdown = Column(Numeric, nullable=False)
    sharpe_ratio = Column(Numeric, nullable=False)
    std_dev = Column(Numeric, nullable=False)
    turnover = Column(Numeric, nullable=False)

class Trade(Base):
    __tablename__ = "trades"
    trade_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    portfolio_id = Column(UUID(as_uuid=True), nullable=False)
    symbol_id = Column(UUID(as_uuid=True), nullable=False)
    traded_at = Column(DateTime(timezone=True), nullable=False)
    trade_type = Column(String, nullable=False)
    order_type = Column(String, nullable=False)
    price = Column(Numeric, nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)


class Portfolio(Base):
    __tablename__ = "portfolios"
    portfolio_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    portfolio_name = Column(String, nullable=False)
    last_updated_at = Column(DateTime(timezone=True), nullable=False)

class Sector(Base):
    __tablename__ = "sectors"
    sector_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    sector_name = Column(String, nullable=False)

class SymbolSector(Base):
    __tablename__ = "symbol_sectors"
    symbol_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    sector_id = Column(UUID(as_uuid=True), nullable=False)
    pct = Column(Numeric, nullable=False)

class Symbol(Base):
    __tablename__ = "symbols"
    symbol_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    symbol = Column(String, nullable=False)
    price = Column(Numeric, nullable=False)
    last_updated_at = Column(DateTime(timezone=True), nullable=False)

