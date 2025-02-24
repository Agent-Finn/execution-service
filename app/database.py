from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import json

# Get and parse PostgreSQL credentials from environment variable
postgres_credentials_str = os.getenv("POSTGRES_CREDENTIALS")
if not postgres_credentials_str:
    raise ValueError("POSTGRES_CREDENTIALS environment variable is required")

try:
    postgres_credentials = json.loads(postgres_credentials_str)
    
    # Determine environment (production or local)
    is_production = os.getenv("NODE_ENV") == "production"
    
    if is_production:
        # Use Cloud SQL Unix socket for production
        host = "/cloudsql/nimble-chess-449208-f3:us-central1:finn-sql"
        connect_args = {"unix_socket": host}  # Cloud SQL uses Unix socket
    else:
        # Use local Docker host
        host = "host.docker.internal"
        connect_args = {"host": host, "port": 5432}  # Explicit port for clarity
    
    # Construct the DATABASE_URL
    DATABASE_URL = (
        f"postgresql://{postgres_credentials['username']}:{postgres_credentials['password']}"
        f"@{host if not is_production else ''}:5432/{postgres_credentials['database']}"
    )
except json.JSONDecodeError:
    raise ValueError("POSTGRES_CREDENTIALS must be a valid JSON string")
except KeyError:
    raise ValueError("POSTGRES_CREDENTIALS must contain username, password, and database fields")

# Create SQLAlchemy engine with connection options
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,  # Use environment-specific connect_args
    pool_pre_ping=True,         # Ensure connection health before use
    pool_size=5,                # Default pool size, adjust as needed
    max_overflow=10,            # Allow some overflow connections
    pool_timeout=30             # Timeout for acquiring a connection
)

# Session factory for synchronous ORM
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

# Optional: Create tables (uncomment to run once during setup)
# Base.metadata.create_all(engine)