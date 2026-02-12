# Fix "Record Expense not working" - Database Connection Pool Issue

## Root Cause
Database connection pool exhaustion - connections aren't being released properly, causing timeouts when recording expenses.

## Plan
- [x] Fix database connection to use NullPool for SQLite
- [x] Fix auth middleware to pass session to handlers
- [x] Update expenses handler to reuse session from middleware
- [x] Update sales handler to reuse session from middleware
- [ ] Test the fix

## Changes Made

### 1. app/database/connection.py ✅
- Use `NullPool` for SQLite since it doesn't benefit from pooling
- This prevents connection exhaustion

### 2. app/middlewares/auth.py ✅
- Store db session in `data['db']` so handlers can reuse it
- Add try/finally to ensure session is properly handled

### 3. app/handlers/expenses.py ✅
- Use session from `data['db']` when available
- Only open new session when needed

### 4. app/handlers/sales.py ✅
- Use session from `data['db']` when available
- Only open new session when needed

