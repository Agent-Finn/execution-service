from fastapi import HTTPException
from datetime import datetime
from ..models import UserCreate, User
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

def create_user(user: UserCreate):
    try:
        with SessionLocal() as session:  # Use SessionLocal instead of Session(engine)
            if session.query(User).filter(User.user_id == user.user_id).first():
                raise HTTPException(status_code=400, detail="User ID already exists")
            if session.query(User).filter(User.email == user.email).first():
                raise HTTPException(status_code=400, detail="Email already exists")

            new_user = User(
                user_id=user.user_id,
                email=user.email,
                name=user.name,
                last_login=datetime.utcnow()
            )
            session.add(new_user)
            session.commit()

            return {"status": "success", "message": "User created successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Failed to create user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")