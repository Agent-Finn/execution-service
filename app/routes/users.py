from fastapi import HTTPException
from sqlalchemy import text
from datetime import datetime
from ..models import UserCreate
from ..database import engine

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