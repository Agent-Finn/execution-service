from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import json

# Get and parse postgres credentials
postgres_credentials_str = os.getenv('POSTGRES_CREDENTIALS')
if not postgres_credentials_str:
    raise ValueError("POSTGRES_CREDENTIALS environment variable is required")

try:
    postgres_credentials = json.loads(postgres_credentials_str)
    
    # Determine if we're in production
    is_production = os.getenv('NODE_ENV') == 'production'
    
    if is_production:
        # Use Cloud SQL connection
        host = f"/cloudsql/nimble-chess-449208-f3:us-central1:finn-sql"
    else:
        # Use local Docker connection
        host = "host.docker.internal"
    
    DATABASE_URL = f"postgresql://{postgres_credentials['username']}:{postgres_credentials['password']}@{host}:5432/{postgres_credentials['database']}"
except json.JSONDecodeError:
    raise ValueError("POSTGRES_CREDENTIALS must be a valid JSON string")
except KeyError:
    raise ValueError("POSTGRES_CREDENTIALS must contain username, password, and database fields")

# Add connection options for better error handling
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "connect_timeout": 5
    },
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base() 