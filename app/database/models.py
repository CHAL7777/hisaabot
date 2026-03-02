from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100))
    full_name = Column(String(200), nullable=False)
    phone = Column(String(20))
    business_name = Column(String(200))
    currency = Column(String(10), default="Rp")
    language = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, name='{self.full_name}')>"

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    currency = Column(String(10), default="Rp")
    timezone = Column(String(64), default="UTC")
    logo_file_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Business(id={self.id}, name='{self.name}', owner={self.owner_user_id})>"

class BusinessMember(Base):
    __tablename__ = "business_members"

    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="staff")  # owner, manager, staff
    status = Column(String(20), nullable=False, default="active")  # active, invited, suspended
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return (
            f"<BusinessMember(id={self.id}, business_id={self.business_id}, "
            f"user_id={self.user_id}, role='{self.role}', status='{self.status}')>"
        )

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(80), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, action='{self.action}', actor={self.actor_user_id})>"

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    product_name = Column(String(200))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float)
    customer_id = Column(Integer, nullable=True)
    payment_method = Column(String(50), default="cash")  # cash, credit, transfer
    notes = Column(Text)
    sale_date = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Sale(id={self.id}, amount={self.amount}, product='{self.product_name}')>"

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)  # supplies, rent, salary, etc.
    description = Column(Text)
    expense_date = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Expense(id={self.id}, amount={self.amount}, category='{self.category}')>"

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True, nullable=True)
    description = Column(Text)
    purchase_price = Column(Float, nullable=True)  # Cost price
    selling_price = Column(Float, nullable=True)   # Selling price
    stock = Column(Integer, default=0)
    min_stock = Column(Integer, default=5)  # Alert when below this
    unit = Column(String(20), default="pcs")
    category = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', stock={self.stock})>"

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    email = Column(String(200), nullable=True)
    address = Column(Text)
    credit_limit = Column(Float, default=0.0)
    credit_balance = Column(Float, default=0.0)
    total_purchases = Column(Float, default=0.0)
    last_purchase = Column(DateTime, nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', balance={self.credit_balance})>"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    customer_id = Column(Integer, nullable=True)
    type = Column(String(50), nullable=False)  # sale, expense, payment, credit
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    reference_id = Column(Integer, nullable=True)  # Links to sale/expense ID
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.type}', amount={self.amount})>"
