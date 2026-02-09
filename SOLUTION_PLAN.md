# PostgreSQL Connection Fix Plan

## Problem Analysis
- **Error**: `Ident authentication failed for user "postgres"`
- **Root Cause**: PostgreSQL is configured to use `ident` authentication method for local connections
- **Affected Files**: 
  - `config.py` - Database configuration
  - `test_db.py` - Connection test script
  - `.env` - Environment variables (needs update)

## Current Configuration
- Database URL: Defaults to SQLite if DB_URL not set
- Database Engine: SQLAlchemy with PostgreSQL support (pg8000, psycopg2-binary)
- Expected DB: PostgreSQL for production use

## Solution Steps

### Step 1: Locate pg_hba.conf
```bash
sudo find /etc/postgresql -name "pg_hba.conf" 2>/dev/null
# Common locations:
# - /etc/postgresql/18/main/pg_hba.conf (Ubuntu/Debian)
# - /var/lib/postgresql/18/main/pg_hba.conf (RHEL/CentOS)
```

### Step 2: Edit pg_hba.conf
```bash
sudo nano /etc/postgresql/18/main/pg_hba.conf
```

**Change authentication method from `ident` to `md5`:**
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                md5
```

### Step 3: Restart PostgreSQL
```bash
sudo systemctl restart postgresql
```

### Step 4: Set PostgreSQL Password
```bash
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'your_secure_password';"
```

### Step 5: Update .env File
```
DB_URL=postgresql://postgres:your_secure_password@localhost/microbiz
```

### Step 6: Test Connection
```bash
python test_db.py
```

## Files to Create/Update

### 1. Create a database setup script
- `scripts/setup_database.py` - Automated database setup

### 2. Update configuration documentation
- Add PostgreSQL setup instructions to README.md

### 3. Create environment template
- `.env.example` - Template for environment variables

## Alternative Solutions

### Option A: Use Peer Authentication
```bash
sudo -u postgres psql
# Then set password if needed
```

### Option B: Switch to Socket Connection
Update DB_URL:
```
DB_URL=postgresql://postgres:@/microbiz?host=/var/run/postgresql
```

### Option C: Use md5 with localhost
Update pg_hba.conf for localhost:
```
host    all             all             127.0.0.1/32            md5
```

## Testing Verification
1. Connection test passes: `python test_db.py`
2. Database tables can be created: `python -c "from app.database.connection import init_db; init_db()"`
3. Bot can connect: Test with `python bot.py`

## Security Considerations
- Use strong password for postgres user
- Limit PostgreSQL access to trusted IPs
- Consider using environment variables for sensitive data
- Regularly update PostgreSQL for security patches

## Rollback Plan
If issues occur:
1. Restore original pg_hba.conf
2. Restart PostgreSQL
3. Revert .env to use SQLite

