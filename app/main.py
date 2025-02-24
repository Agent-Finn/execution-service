from fastapi import FastAPI
from dotenv import load_dotenv
from .routes import core, users, portfolio, position, portfolio_stats, get_stock_price

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
app.get("/allocations")(portfolio.get_allocations_by_portfolio)

# Position routes
app.get("/positions")(position.get_positions_by_portfolio)

# Portfolio stats routes
app.get("/portfolio-stats")(portfolio_stats.get_portfolio_stats_by_portfolio)

app.get("/stock-prices")(get_stock_price.get_stock_price)