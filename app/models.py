from pydantic import BaseModel, EmailStr

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