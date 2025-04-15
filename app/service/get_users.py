from fastapi import HTTPException
from datetime import datetime
from ..models import User
from ..database import engine, SessionLocal  # Import SessionLocal

def get_users():
    try:
        with SessionLocal() as session:  # Use SessionLocal instead of Session(engine)
            users = session.query(User).all()
            users_list = [
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "name": user.name,
                }
                for user in users
            ]
            return {"users": users_list}
    except Exception as e:
        print(f"Failed to fetch users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")

