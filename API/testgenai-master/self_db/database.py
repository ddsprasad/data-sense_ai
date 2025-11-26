from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# engine = create_engine(settings.self_database_url)
engine = create_engine(
    settings.self_database_url,
    echo=False,
    connect_args={
        "autocommit": False,
        "connect_timeout": 30,
    },
    pool_pre_ping=True,
    pool_size=25,
    pool_recycle=3600,
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