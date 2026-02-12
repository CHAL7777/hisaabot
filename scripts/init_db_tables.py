#!/usr/bin/env python3
"""
Initialize database tables
Creates all tables defined in app.database.models
"""
import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from config import db_config
from app.database.connection import engine
from app.database.models import Base, User, Sale, Expense, Product, Customer, Transaction


def init_db_sync():
    """Synchronous version of init_db"""
    Base.metadata.create_all(bind=engine)


def main():
    """Initialize database tables"""
    print("=" * 60)
    print("DATABASE TABLE INITIALIZATION")
    print("=" * 60)
    print()
    
    # Step 1: Initialize database tables
    print("[1/3] Creating database tables...")
    init_db_sync()
    print("✓ Tables created successfully!")
    print()
    
    # Step 2: List all tables
    print("[2/3] Verifying created tables...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"✓ Found {len(tables)} tables in database")
    print()
    
    # Step 3: Show table details
    print("[3/3] Table Details:")
    print("-" * 60)
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"\n📋 Table: {table}")
        for col in columns:
            nullable = "" if col['nullable'] else " (NOT NULL)"
            primary = " [PK]" if col['primary_key'] else ""
            print(f"   - {col['name']}: {col['type']}{nullable}{primary}")
    
    print()
    print("=" * 60)
    print("✓ DATABASE INITIALIZATION COMPLETE!")
    print("=" * 60)
    
    return tables


if __name__ == "__main__":
    main()

