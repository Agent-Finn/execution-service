from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import User
from typing import Optional
import uuid
from datetime import datetime
import pytz

async def add_user(email: str, name: str, clerk_id: str) -> Optional[User]:
    """
    Add a user to the users table.

    Args:
        email (str): The email of the user.
        name (str): The name of the user.
        clerk_id (str): The clerk ID of the user.

    Returns:
        Optional[User]: The newly created User object if added, None on error.
    """
    try:
        with SessionLocal() as session:
            # Clear the session cache to ensure we have the latest database state
            session.expire_all()
            
            # Check if user with this email already exists
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                print(f"User with email '{email}' already exists.")
                return None
            
            # Create a new user with a generated UUID
            pst = pytz.timezone('America/Los_Angeles')
            current_time = datetime.now(pst)
            
            # Create the new user
            new_user = User(
                user_id=uuid.uuid4(),
                email=email,
                name=name,
                last_login_at=current_time,
                clerk_id=clerk_id
            )
            
            session.add(new_user)
            session.commit()
            
            # Refresh the object to ensure all attributes are loaded
            session.refresh(new_user)
            
            print(f"User '{name}' with email '{email}' added successfully.")
            return new_user
    except Exception as e:
        print(f"Error adding user '{name}' with email '{email}': {str(e)}")
        return None 