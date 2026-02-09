#!/usr/bin/env python3
"""
Quick Database Connection Test
Tests both SQLite and PostgreSQL connections
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_sqlite():
    """Test SQLite connection"""
    from sqlalchemy import create_engine, text
    from config import db_config
    
    # Force SQLite for testing
    sqlite_url = "sqlite:///microbiz_test.db"
    try:
        engine = create_engine(sqlite_url, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text('SELECT sqlite_version()'))
            version = result.fetchone()[0]
            print(f"✓ SQLite Version: {version}")
            print("✓ SQLite connection successful!")
            return True
    except Exception as e:
        print(f"✗ SQLite connection failed: {e}")
        return False

def test_postgresql():
    """Test PostgreSQL connection"""
    from sqlalchemy import create_engine, text
    from config import db_config
    
    if not db_config.URL or "sqlite" in db_config.URL:
        print("⚠ PostgreSQL URL not configured (DB_URL not set or using SQLite)")
        return None
    
    try:
        engine = create_engine(db_config.URL, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            print(f"✓ PostgreSQL Version: {version}")
            print("✓ PostgreSQL connection successful!")
            return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        print("\nTo fix PostgreSQL connection:")
        print("1. Run: python scripts/database_setup.py")
        print("2. Follow the PostgreSQL setup guide")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("Database Connection Test")
    print("=" * 50)
    
    print("\n[1] Testing SQLite (fallback):")
    sqlite_ok = test_sqlite()
    
    print("\n[2] Testing PostgreSQL:")
    pg_ok = test_postgresql()
    
    print("\n" + "=" * 50)
    if sqlite_ok:
        print("✓ At least SQLite connection works")
        if pg_ok:
            print("✓ PostgreSQL connection also works!")
        else:
            print("→ PostgreSQL needs configuration")
    else:
        print("✗ No database connection available")
    print("=" * 50)

if __name__ == "__main__":
    main()

