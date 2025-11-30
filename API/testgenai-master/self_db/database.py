from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Optimized engine with better connection pooling
engine = create_engine(
    settings.self_database_url,
    echo=False,
    connect_args={
        "autocommit": False,
        "connect_timeout": 10,  # Reduced from 30
    },
    pool_pre_ping=True,
    pool_size=10,  # Active connections
    max_overflow=20,  # Extra connections when needed
    pool_recycle=1800,  # Recycle connections every 30 min
    pool_timeout=10,  # Wait max 10s for connection
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()