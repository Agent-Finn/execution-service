from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base

# SQLAlchemy Base
Base = declarative_base()

# SQLAlchemy Model for users table
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, unique=True, nullable=False, primary_key=True)     # Custom user_id from UserCreate
    email = Column(String, unique=True, nullable=False)        # Email with uniqueness constraint
    name = Column(String, nullable=False)                      # Name field
    last_login = Column(DateTime, nullable=True)    
    
    # SQLAlchemy Model for allocation table
class Allocation(Base):
    __tablename__ = "allocation"
    allocation_id = Column(Integer, primary_key=True)  # SERIAL maps to Integer with autoincrement
    portfolio_id = Column(Integer, nullable=False)     # Foreign key to portfolios
    recommendation_date = Column(DateTime, nullable=True)  # TIMESTAMP
    symbol = Column(String(10), nullable=True)         # VARCHAR(10)
    target_pct = Column(Numeric(5, 2), nullable=True)  # NUMERIC(5,2)           # For create_user

class Position(Base):
    __tablename__ = "positions"
    position_id = Column(Integer, nullable=False, primary_key=True)
    portfolio_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    symbol = Column(String, nullable=True)
    quantity = Column(Integer, nullable=False)
    last_updated = Column(DateTime, nullable=True)

    # SQLAlchemy Model for portfolio_stats table
class PortfolioStats(Base):
    __tablename__ = "portfolio_stats"
    stat_id = Column(Integer, primary_key=True)          # Primary key
    portfolio_id = Column(Integer, nullable=False)       # Foreign key to portfolios
    portfolio_value = Column(Numeric, nullable=False)    # Numeric value, assume precision/scale as needed
    stat_date = Column(DateTime, nullable=True)         # Timestamp
    alpha = Column(Numeric, nullable=False)             # Numeric value
    beta = Column(Numeric, nullable=False)              # Numeric value
    max_drawdown = Column(Numeric, nullable=False)      # Numeric value
    sharpe_ratio = Column(Numeric, nullable=False)      # Numeric value
    std_dev = Column(Numeric, nullable=False)           # Numeric value
    turnover = Column(Numeric, nullable=False)          # Numeric value
    

class UserCreate(BaseModel):
    user_id: int
    email: EmailStr
    name: str

class PositionCreate(BaseModel):
    position_id: int
    portfolio_id: int
    portfolio_name: str
    user_id: int
    stock: str
    quantity: int