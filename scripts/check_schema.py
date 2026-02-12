#!/usr/bin/env python3
"""Check database schema - lists all tables, columns, and relationships"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text
from config import db_config
from app.database.models import Base


def check_database_connection():
    """Test and display database connection info"""
    print("=" * 60)
    print("DATABASE CONNECTION CHECK")
    print("=" * 60)
    
    engine = create_engine(db_config.URL, echo=False)
    
    try:
        with engine.connect() as conn:
            if db_config.URL.startswith("sqlite"):
                result = conn.execute(text('SELECT sqlite_version()'))
                version = result.fetchone()[0]
                print(f"✓ Database: SQLite")
                print(f"✓ SQLite Version: {version}")
            else:
                result = conn.execute(text('SELECT version()'))
                version = result.fetchone()[0]
                print(f"✓ Database: PostgreSQL")
                print(f"✓ Version: {version}")
            print("✓ Connection: SUCCESS")
            return engine
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return None


def list_tables(engine):
    """List all tables in the database"""
    print("\n" + "=" * 60)
    print("DATABASE TABLES")
    print("=" * 60)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if not tables:
        print("⚠ No tables found in database!")
        return []
    
    print(f"Found {len(tables)} table(s):\n")
    for i, table in enumerate(tables, 1):
        print(f"  {i}. {table}")
    
    return tables


def show_table_schema(engine, table_name):
    """Show detailed schema for a single table"""
    inspector = inspect(engine)
    
    print(f"\n{'─' * 60}")
    print(f"Table: {table_name}")
    print(f"{'─' * 60}")
    
    # Get columns
    columns = inspector.get_columns(table_name)
    print(f"\nColumns ({len(columns)}):")
    print(f"  {'Name':<25} {'Type':<20} {'Nullable':<10} {'Default'}")
    print(f"  {'─' * 23} {'─' * 18} {'─' * 8} {'─'}")
    
    for col in columns:
        name = col['name']
        type_ = str(col['type'])
        nullable = str(col['nullable'])
        default = str(col.get('default', 'None'))[:20]
        print(f"  {name:<25} {type_:<20} {nullable:<10} {default}")
    
    # Get primary key
    pks = inspector.get_pk_constraint(table_name)
    if pks['constrained_columns']:
        print(f"\nPrimary Key: {', '.join(pks['constrained_columns'])}")
    
    # Get foreign keys
    fks = inspector.get_foreign_keys(table_name)
    if fks:
        print(f"\nForeign Keys:")
        for fk in fks:
            print(f"  {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    # Get indexes
    indexes = inspector.get_indexes(table_name)
    if indexes:
        print(f"\nIndexes:")
        for idx in indexes:
            if idx['unique']:
                print(f"  ✓ {idx['name']} (UNIQUE) on {idx['column_names']}")
            else:
                print(f"  • {idx['name']} on {idx['column_names']}")


def show_model_definitions():
    """Show the SQLAlchemy model class definitions"""
    print("\n" + "=" * 60)
    print("SQLALCHEMY MODEL DEFINITIONS")
    print("=" * 60)
    
    from app.database.models import User, Sale, Expense, Product, Customer, Transaction
    
    models = [
        ("users", User),
        ("sales", Sale),
        ("expenses", Expense),
        ("products", Product),
        ("customers", Customer),
        ("transactions", Transaction),
    ]
    
    for table_name, model in models:
        print(f"\n{'─' * 60}")
        print(f"Model: {model.__name__}")
        print(f"{'─' * 60}")
        print(f"  __tablename__: '{table_name}'")
        print("\n  Columns:")
        
        for column in model.__table__.columns:
            col_type = type(column.type).__name__
            nullable = "nullable=True" if column.nullable else "nullable=False"
            primary = "primary_key=True" if column.primary_key else ""
            unique = "unique=True" if column.unique else ""
            
            opts = [nullable, primary, unique]
            opts_str = ", ".join([o for o in opts if o])
            
            print(f"    {column.name}: {col_type} ({opts_str})")


def show_er_diagram():
    """Show simplified ER diagram"""
    print("\n" + "=" * 60)
    print("ENTITY RELATIONSHIP DIAGRAM")
    print("=" * 60)
    
    print("""
    ┌─────────────┐       ┌─────────────┐
    │    users    │       │  customers  │
    ├─────────────┤       ├─────────────┤
    │ id (PK)     │       │ id (PK)     │
    │ telegram_id │1    N │ name        │
    │ full_name   │──<──>│ phone       │
    └─────────────┘       │ credit_*    │
         │                └─────────────┘
         │                     ▲
         │ N                   │
         ▼                     │ N
    ┌─────────────┐       ┌─────────────┐
    │   sales     │       │  customers  │
    ├─────────────┤       │ (in sales)  │
    │ id (PK)     │       └─────────────┘
    │ user_id (FK)│            │
    │ amount      │            │
    │ product_*   │            ▼
    │ customer_id │       ┌─────────────┐
    └─────────────┘       │transactions│
         │                ├─────────────┤
         │ N              │ id (PK)     │
         ▼                │ user_id (FK)│
    ┌─────────────┐       │ customer_id │
    │  expenses   │       │ type        │
    ├─────────────┤       │ amount      │
    │ id (PK)     │       │ balance_*   │
    │ user_id (FK)│       └─────────────┘
    │ amount      │
    │ category    │       ┌─────────────┐
    └─────────────┘       │  products   │
                          ├─────────────┤
                          │ id (PK)     │
                          │ user_id (FK)│
                          │ name        │
                          │ price_*     │
                          │ stock       │
                          └─────────────┘
    """)


def show_create_statements(engine):
    """Show raw CREATE TABLE statements"""
    print("\n" + "=" * 60)
    print("RAW CREATE TABLE STATEMENTS")
    print("=" * 60)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    for table in tables:
        print(f"\n--- {table} ---")
        try:
            # Get create statement
            create_stmt = inspector.get_table_comment(table)
            print(f"Table comment: {create_stmt.get('text', 'N/A')}")
        except:
            pass


def main():
    """Main function to run all schema checks"""
    print("\n" + "█" * 60)
    print("   DATABASE SCHEMA CHECKER")
    print("   " + db_config.URL)
    print("█" * 60)
    
    # 1. Check connection
    engine = check_database_connection()
    if not engine:
        print("\n❌ Cannot proceed without database connection.")
        sys.exit(1)
    
    # 2. List tables
    tables = list_tables(engine)
    
    # 3. Show schema for each table
    if tables:
        print("\n" + "=" * 60)
        print("TABLE SCHEMAS")
        print("=" * 60)
        for table in tables:
            show_table_schema(engine, table)
    
    # 4. Show model definitions
    show_model_definitions()
    
    # 5. Show ER diagram
    show_er_diagram()
    
    # 6. Show create statements
    show_create_statements(engine)
    
    print("\n" + "=" * 60)
    print("SCHEMA CHECK COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

