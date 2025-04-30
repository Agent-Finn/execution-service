from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from ..service.add_user import add_user

# Define request model
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    clerk_id: str

# Create router
router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.post("/", response_model=dict)
async def create_user(user: UserCreate):
    """
    Add a new user.

    Args:
        user (UserCreate): The user details including email, name, and clerk_id

    Returns:
        dict: A dictionary containing the user details if added successfully

    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        result = await add_user(user.email, user.name, user.clerk_id)
        if result:
            return {
                "user_id": str(result.user_id),
                "email": result.email,
                "name": result.name,
                "last_login_at": result.last_login_at,
                "clerk_id": result.clerk_id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"User with email '{user.email}' already exists or could not be created"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error adding user: {str(e)}"
        ) 