# Database Troubleshooting Guide

## PostgreSQL Connection Issues

### Error: "Ident authentication failed for user postgres"

This is the most common PostgreSQL connection error. It occurs when PostgreSQL is configured to use `ident` authentication instead of `md5` or `password`.

#### Root Cause
The `ident` authentication method checks the OS username against the PostgreSQL username. When connecting as `postgres` user from your application, the OS user is different, causing authentication failure.

#### Solution

##### Step 1: Find and edit pg_hba.conf

**Find the file:**
```bash
sudo find /etc/postgresql -name "pg_hba.conf"
```

**Common locations:**
- Ubuntu/Debian: `/etc/postgresql/18/main/pg_hba.conf`
- RHEL/CentOS: `/var/lib/postgresql/18/main/data/pg_hba.conf`
- macOS (Homebrew): `/opt/homebrew/var/postgres/pg_hba.conf`

**Edit the file:**
```bash
sudo nano /etc/postgresql/18/main/pg_hba.conf
```

**Change these lines:**
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                ident
```

**To:**
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                md5
host    all             all             127.0.0.1/32            md5
```

##### Step 2: Restart PostgreSQL

```bash
sudo systemctl restart postgresql
```

##### Step 3: Set postgres user password

```bash
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'your_strong_password';"
```

##### Step 4: Update your .env file

```
DB_URL=postgresql://postgres:your_strong_password@localhost/microbiz
```

##### Step 5: Test connection

```bash
python test_db.py
```

---

### Alternative Solutions

#### Option A: Use Peer Authentication

If you prefer to keep ident but create a matching system user:

```bash
# Create a system user matching PostgreSQL user
sudo adduser postgres

# Then you can connect without password
sudo -u postgres psql
```

#### Option B: Use Socket Connection

Update your `.env`:
```
DB_URL=postgresql://postgres@/%2Fvar%2Frun%2Fpostgresql/microbiz
```

Or use connection with socket:
```
DB_URL=postgresql://postgres:password@/microbiz?host=/var/run/postgresql
```

#### Option C: Trust Authentication (Not Recommended)

Change pg_hba.conf to use `trust` (only for local development):
```
local   all   all   trust
```

⚠️ **Warning**: This allows any local user to connect without authentication. Only use for local development!

---

### Testing Different Authentication Methods

#### Test 1: Local socket connection
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://postgres:password@/microbiz?host=/tmp")
```

#### Test 2: TCP connection to localhost
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://postgres:password@127.0.0.1/microbiz")
```

#### Test 3: With explicit port
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://postgres:password@localhost:5432/microbiz")
```

---

### PostgreSQL Service Management

#### Check PostgreSQL status
```bash
systemctl status postgresql
```

#### Start PostgreSQL
```bash
sudo systemctl start postgresql
```

#### Stop PostgreSQL
```bash
sudo systemctl stop postgresql
```

#### Restart PostgreSQL
```bash
sudo systemctl restart postgresql
```

#### Check PostgreSQL logs
```bash
sudo journalctl -u postgresql -f
```

---

### Verify PostgreSQL Configuration

#### Check listen_addresses
```bash
sudo -u postgres psql -c "SHOW listen_addresses;"
```

Should return `localhost` or `127.0.0.1`

#### Check authentication settings
```bash
sudo -u postgres psql -c "SHOW hba_file;"
```

#### Reload configuration without restart
```bash
sudo systemctl reload postgresql
```

---

### Using the Helper Scripts

We've provided helper scripts to make database setup easier:

#### Quick Connection Test
```bash
python scripts/quick_test.py
```

This tests both SQLite and PostgreSQL connections.

#### Database Setup Guide
```bash
python scripts/database_setup.py
```

This provides step-by-step PostgreSQL setup instructions.

---

### Connection Troubleshooting Checklist

- [ ] PostgreSQL service is running
- [ ] pg_hba.conf has correct authentication method
- [ ] PostgreSQL has been restarted after config changes
- [ ] postgres user has a password set
- [ ] .env file has correct DB_URL
- [ ] Firewall allows connections on port 5432 (if using TCP)
- [ ] PostgreSQL is listening on correct interface
- [ ] Database 'microbiz' exists (or will be created)

---

### Create Database If Not Exists

```sql
CREATE DATABASE microbiz;
```

Or from command line:
```bash
sudo -u postgres createdb microbiz
```

---

### Advanced: Multiple PostgreSQL Versions

If you have multiple PostgreSQL versions installed:

```bash
# Find all versions
ls /etc/postgresql/

# Check which is active
pg_lsclusters

# Manage specific version
sudo systemctl status postgresql@18-main
```

---

### Getting Help

If you still have issues:

1. Check PostgreSQL logs:
   ```bash
   sudo tail -f /var/log/postgresql/postgresql-18-main.log
   ```

2. Test basic PostgreSQL connection:
   ```bash
   sudo -u postgres psql -c "SELECT 1;"
   ```

3. Verify network connectivity:
   ```bash
   nc -zv localhost 5432
   ```

