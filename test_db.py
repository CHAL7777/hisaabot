#!/usr/bin/env python3
"""Test database connection"""
from sqlalchemy import create_engine, text
from config import db_config

# Create engine
engine = create_engine(db_config.URL, echo=False)

# Test connection
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        print('PostgreSQL Version:', result.fetchone()[0])
        print('Connection successful!')
except Exception as e:
    print(f'Connection failed: {e}')

