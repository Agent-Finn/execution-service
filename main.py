from app.service import get_allocations_portfolio, get_users
from fastapi import FastAPI
from app.routes import health

app = FastAPI()

# Include routers
app.include_router(health.router)
app.include_router(get_users.router)
app.include_router(get_allocations_portfolio.router) 