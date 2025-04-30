from .service import get_allocations_portfolio, get_portfolio_stats, get_positions, get_users
from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from .routes import core, get_stock_price_router, to_sell_router, update_stock_price_router
from .routes.sector_routers import router as sector_router
from .routes.add_symbol_router import router as symbol_router
from .routes.add_portfolio_router import router as portfolio_router
from .routes.add_user_router import router as user_router
from .routes.update_portfolio_balance_router import router as portfolio_balance_router
from .routes.get_portfolio_symbol_allocation_router import router as portfolio_symbol_allocation_router
from .routes.symbol_sector_router import router as symbol_sector_router
from .routes.populate_symbol_sectors_router import router as populate_symbol_sectors_router
from app.routes import execute_trade_router, update_positions_router
from .routes.execute_full_trade_router import router as execute_full_trade_router
from .routes.add_allocation_router import router as add_allocation_router
from .routes.random_allocation_router import router as random_allocation_router
from .routes.backtest_allocations_router import router as backtest_allocations_router
from .routes.industries import router as industries_router
from .routes.sectors import router as new_sectors_router
from .routes.import_symbol_prices_router import router as import_symbol_prices_router

# Load environment variables from .env file if it exists
load_dotenv()

app = FastAPI()

# Core routes
app.get("/")(core.root)
app.get("/health")(core.health_check)

# Create router for Utils endpoints
utils_router = APIRouter(tags=["Utils"])

# Add routes to utils_router
utils_router.get("/users", response_model=dict)(get_users.get_users)
utils_router.get("/allocations", response_model=dict)(get_allocations_portfolio.get_allocations_by_portfolio)
utils_router.get("/positions", response_model=dict)(get_positions.get_positions_by_portfolio)
utils_router.get("/portfolio-stats", response_model=dict)(get_portfolio_stats.get_portfolio_stats_by_portfolio)
utils_router.get("/stock-prices")(get_stock_price_router.get_stock_price)

# Include all routers
app.include_router(utils_router)
app.include_router(to_sell_router.router)
app.include_router(update_stock_price_router.router)
app.include_router(update_positions_router.router)
app.include_router(sector_router)
app.include_router(symbol_router)
app.include_router(portfolio_router)
app.include_router(user_router)
app.include_router(execute_trade_router.router)
app.include_router(execute_full_trade_router)
app.include_router(portfolio_balance_router)
app.include_router(portfolio_symbol_allocation_router)
app.include_router(symbol_sector_router)
app.include_router(populate_symbol_sectors_router)
app.include_router(add_allocation_router)
app.include_router(random_allocation_router)
app.include_router(backtest_allocations_router)
app.include_router(industries_router)
app.include_router(new_sectors_router)
app.include_router(import_symbol_prices_router)