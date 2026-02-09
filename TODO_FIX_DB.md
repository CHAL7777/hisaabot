# PostgreSQL Connection Fix - TODO List

## Status: Documentation and Scripts Created ✅

### Completed Steps

- [x] Analyze codebase structure and dependencies
- [x] Read config.py, test_db.py, and connection.py
- [x] Review requirements.txt for database drivers
- [x] Create SOLUTION_PLAN.md with comprehensive fix steps
- [x] Create .env.example template
- [x] Create scripts/database_setup.py helper script
- [x] Create scripts/quick_test.py for connection testing
- [x] Create DATABASE_TROUBLESHOOTING.md guide
- [x] Update README.md with PostgreSQL setup instructions

### Manual Steps Required

- [ ] Step 1: Find pg_hba.conf location
  ```bash
  sudo find /etc/postgresql -name "pg_hba.conf"
  ```

- [ ] Step 2: Edit pg_hba.conf (requires sudo)
  - Change `ident` to `md5` for postgres user
  - Location: `/etc/postgresql/18/main/pg_hba.conf`

- [ ] Step 3: Restart PostgreSQL
  ```bash
  sudo systemctl restart postgresql
  ```

- [ ] Step 4: Set postgres password
  ```bash
  sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'your_password';"
  ```

- [ ] Step 5: Create .env file from template
  ```bash
  cp .env.example .env
  # Edit .env with your BOT_TOKEN and DB_URL
  ```

- [ ] Step 6: Test database connection
  ```bash
  python scripts/quick_test.py
  # OR
  python test_db.py
  ```

- [ ] Step 7: Initialize database tables
  ```bash
  python -c "from app.database.connection import init_db; init_db()"
  ```

- [ ] Step 8: Start the bot
  ```bash
  python bot.py
  ```

### Quick Verification Commands

```bash
# Check PostgreSQL status
systemctl status postgresql

# Test basic PostgreSQL connection
sudo -u postgres psql -c "SELECT 1;"

# Check PostgreSQL version
psql --version

# List databases
sudo -u postgres psql -l

# View PostgreSQL configuration
sudo -u postgres psql -c "SHOW hba_file;"
```

### Environment Setup Commands

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Test database connection
python scripts/quick_test.py

# Start bot
python bot.py
```

### Files Created

1. **SOLUTION_PLAN.md** - Overview of the problem and solution
2. **DATABASE_TROUBLESHOOTING.md** - Comprehensive troubleshooting guide
3. **.env.example** - Environment variables template
4. **scripts/database_setup.py** - Interactive setup helper
5. **scripts/quick_test.py** - Quick connection tester
6. **README.md** - Updated with PostgreSQL setup section

### Alternative: Use SQLite for Development

If you want to avoid PostgreSQL setup for development:

1. No changes to pg_hba.conf needed
2. Use default .env:
   ```env
   DB_URL=sqlite:///microbiz.db
   ```
3. Test connection:
   ```bash
   python scripts/quick_test.py
   ```

This will work immediately without any PostgreSQL configuration.

### PostgreSQL Setup Time Estimate

- Finding pg_hba.conf: 1 minute
- Editing pg_hba.conf: 5 minutes
- Restart PostgreSQL: 1 minute
- Setting password: 2 minutes
- Testing connection: 2 minutes

**Total: ~11 minutes** for PostgreSQL setup

**SQLite Setup: ~1 minute** (just copy .env and run)

