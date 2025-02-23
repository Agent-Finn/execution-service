from fastapi import APIRouter
from sqlalchemy import text
from ..database import engine

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Service is running"}

@router.get("/health")
async def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            connection.commit()
            return {"status": "healthy"}
    except Exception as e:
        print(f"Database health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}, 500 