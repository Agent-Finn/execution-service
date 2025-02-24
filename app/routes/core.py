from fastapi import HTTPException
from sqlalchemy import text
from ..database import engine

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

