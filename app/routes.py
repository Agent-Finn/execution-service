from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import json
from datetime import datetime
from .models import UserCreate, PositionCreate

# Get and parse postgres credentials
postgres_credentials_str = os.getenv('POSTGRES_CREDENTIALS')
if not postgres_credentials_str:
    raise ValueError("POSTGRES_CREDENTIALS environment variable is required")

try:
    postgres_credentials = json.loads(postgres_credentials_str)
    
    # Determine if we're in production
    is_production = os.getenv('NODE_ENV') == 'production'
    
    if is_production:
        # Use Cloud SQL connection
        host = f"/cloudsql/nimble-chess-449208-f3:us-central1:finn-sql"
    else:
        # Use local Docker connection
        host = "host.docker.internal"
    
    DATABASE_URL = f"postgresql://{postgres_credentials['username']}:{postgres_credentials['password']}@{host}:5432/{postgres_credentials['database']}"
except json.JSONDecodeError:
    raise ValueError("POSTGRES_CREDENTIALS must be a valid JSON string")
except KeyError:
    raise ValueError("POSTGRES_CREDENTIALS must contain username, password, and database fields")

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

async def root():
    return {"message": "Service is running"}

async def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            connection.commit()
            return {"status": "healthy"}
    except Exception as e:
        print(f"Database health check failed: {str(e)}")  # This will show in your logs
        return {"status": "unhealthy", "error": str(e)}, 500 

async def get_users():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM users"))
            rows = result.fetchall()
            
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