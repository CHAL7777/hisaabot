#!/usr/bin/env python3
"""
Database Setup Helper Script
Helps with PostgreSQL connection setup and testing
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, shell=True):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=True, text=True, check=False
        )
        return result.stdout + result.stderr, result.returncode
    except Exception as e:
        return str(e), 1

def find_pg_hba_conf():
    """Find pg_hba.conf location"""
    locations = [
        "/etc/postgresql/*/main/pg_hba.conf",
        "/var/lib/postgresql/*/data/pg_hba.conf",
        "/etc/postgresql/pg_hba.conf",
    ]
    
    for loc in locations:
        output, _ = run_command(f"find {loc.replace('*', '*')} -name 'pg_hba.conf' 2>/dev/null | head -1")
        if output.strip():
            return output.strip()
    
    return None

def check_postgresql_status():
    """Check if PostgreSQL is running"""
    output, code = run_command("systemctl is-active postgresql")
    return "active" in output.lower(), output.strip()

def test_connection():
    """Test database connection"""
    from sqlalchemy import create_engine, text
    from config import db_config
    
    try:
        engine = create_engine(db_config.URL, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            print(f"✓ PostgreSQL Version: {version}")
            print("✓ Connection successful!")
            return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def setup_postgresql_guide():
    """Provide setup instructions"""
    print("""
PostgreSQL Setup Guide
======================

Step 1: Locate pg_hba.conf
--------------------------
Run: sudo find /etc/postgresql -name "pg_hba.conf"
Common locations:
- /etc/postgresql/18/main/pg_hba.conf (Ubuntu/Debian)
- /var/lib/postgresql/18/main/pg_hba.conf (RHEL/CentOS)

Step 2: Edit pg_hba.conf
------------------------
Change authentication method from 'ident' to 'md5':
    local   all   postgres   md5
    host    all   all        127.0.0.1/32   md5

Step 3: Restart PostgreSQL
---------------------------
Run: sudo systemctl restart postgresql

Step 4: Set postgres password
------------------------------
Run: sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'your_password';"

Step 5: Update .env file
------------------------
DB_URL=postgresql://postgres:your_password@localhost/microbiz

Step 6: Test connection
-----------------------
Run: python scripts/database_setup.py --test
""")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--test', '-t']:
            test_connection()
            return
        elif sys.argv[1] in ['--help', '-h']:
            print(__doc__)
            return
    
    # Check PostgreSQL status
    is_active, status = check_postgresql_status()
    print(f"PostgreSQL Status: {status}")
    
    # Find pg_hba.conf
    pg_hba = find_pg_hba_conf()
    if pg_hba:
        print(f"pg_hba.conf found: {pg_hba}")
    else:
        print("pg_hba.conf not found in common locations")
    
    # Show setup guide
    setup_postgresql_guide()

if __name__ == "__main__":
    main()

