from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from config import db_config
import asyncio

# Database engine - supports both SQLite and PostgreSQL
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
    async with engine.begin() as conn:
        # For async, use: await conn.run_sync(Base.metadata.create_all)
        Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()