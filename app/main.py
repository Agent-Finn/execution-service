from fastapi import FastAPI
from dotenv import load_dotenv
from .routes import core, users, portfolio

# Load environment variables from .env file if it exists
load_dotenv()

app = FastAPI()

# Core routes
app.get("/")(core.root)
app.get("/health")(core.health_check)

# User routes
app.get("/users")(users.get_users)
app.post("/users")(users.create_user)

# Portfolio routes
app.get("/portfolio-value")(portfolio.get_portfolio_value)