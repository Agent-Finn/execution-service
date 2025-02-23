from fastapi import FastAPI
from app.routes import health, users, portfolio

app = FastAPI()

# Include routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(portfolio.router) 