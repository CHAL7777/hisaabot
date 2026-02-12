from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from config import db_config

# Database engine - supports both SQLite and PostgreSQL
# Use NullPool for SQLite since it doesn't benefit from connection pooling
# and NullPool prevents connection exhaustion issues
if db_config.URL.startswith('sqlite'):
    engine = create_engine(
        db_config.URL,
        echo=db_config.ECHO,
        poolclass=NullPool  # No pooling for SQLite
    )
else:
    engine = create_engine(
        db_config.URL,
        echo=db_config.ECHO,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

async def init_db():
    """Initialize database tables"""
    from .models import Base
    # Use run_sync for synchronous engine
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session (for async context managers)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager for synchronous database sessions.
    
    Usage:
        with get_db_session() as db:
            user = get_user(db, telegram_id)
            # session automatically closed after use
    
    This ensures proper connection pool management and prevents
    connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
