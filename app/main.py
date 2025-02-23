from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from datetime import datetime

# Load environment variables from .env file if it exists
load_dotenv()

app = FastAPI()

# Use the direct DATABASE_URL environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

print(f"Using connection string: {DATABASE_URL}")

# Add connection options for better error handling
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "connect_timeout": 5
    },
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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

@app.get("/")
async def root():
    return {"message": "Service is running"}

@app.get("/health")
async def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            connection.commit()
            return {"status": "healthy"}
    except Exception as e:
        print(f"Database health check failed: {str(e)}")  # This will show in your logs
        return {"status": "unhealthy", "error": str(e)}, 500 

@app.get("/users")
async def get_users():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM users"))
            rows = result.fetchall()
            
            # Convert rows to dictionaries with proper column names
            users = [
                {
                    "id": row[0],
                    "email": row[1],
                    "name": row[2],
                    "created_at": row[3].isoformat() if row[3] else None
                }
                for row in rows
            ]
            return {"users": users}
    except Exception as e:
        print(f"Failed to fetch users: {str(e)}")
        return {"status": "error", "error": str(e)}, 500 

@app.get("/portfolio-value")
async def get_portfolio_value():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT portfolio_value FROM portfolio_stats ORDER BY created_at DESC LIMIT 1"))
            row = result.fetchone()
            
            if row is None:
                raise HTTPException(status_code=404, detail="No portfolio value found")
                
            return {"portfolio_value": row[0]}
    except Exception as e:
        print(f"Failed to fetch portfolio value: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users")
async def create_user(user: UserCreate):
    try:
        with engine.connect() as connection:
            # Check if user_id already exists
            result = connection.execute(
                text("SELECT 1 FROM users WHERE user_id = :user_id"),
                {"user_id": user.user_id}
            )
            if result.fetchone():
                raise HTTPException(status_code=400, detail="User ID already exists")
            
            # Check if email already exists
            result = connection.execute(
                text("SELECT 1 FROM users WHERE email = :email"),
                {"email": user.email}
            )
            if result.fetchone():
                raise HTTPException(status_code=400, detail="Email already exists")
            
            # Insert new user
            connection.execute(
                text("INSERT INTO users (user_id, email, name, last_login) VALUES (:user_id, :email, :name, :last_login)"),
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "name": user.name,
                    "last_login": datetime.utcnow()
                }
            )
            connection.commit()
            
            return {"status": "success", "message": "User created successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Failed to create user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))