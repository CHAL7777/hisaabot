#!/usr/bin/env python3
"""Initialize database tables"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database.connection import init_db
from sqlalchemy import inspect

def main():
    print("Initializing database tables...")
    init_db()
    print("Database tables created successfully!")
    
    # Verify tables were created
    from sqlalchemy import create_engine
    from config import db_config
    engine = create_engine(db_config.URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nCreated tables: {', '.join(tables)}")

if __name__ == "__main__":
    main()
