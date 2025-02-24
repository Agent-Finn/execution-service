from fastapi import FastAPI
from dotenv import load_dotenv
from . import routes

# Load environment variables from .env file if it exists
load_dotenv()

app = FastAPI()

# Register routes
app.get("/")(routes.root)
app.get("/health")(routes.health_check)
app.get("/users")(routes.get_users)
app.get("/portfolio-value")(routes.get_portfolio_value)
app.post("/users")(routes.create_user)