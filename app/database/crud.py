from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from datetime import datetime, date, timedelta
from typing import List, Optional
from .models import User, Sale, Expense, Product, Customer, Transaction

# User CRUD
def get_user(db: Session, telegram_id: int) -> Optional[User]:
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def create_user(db: Session, telegram_id: int, full_name: str, 
                username: Optional[str] = None) -> User:
    user = User(
        telegram_id=telegram_id,
        full_name=full_name,
        username=username
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, telegram_id: int, **kwargs) -> Optional[User]:
    user = get_user(db, telegram_id)
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

# Sale CRUD
def create_sale(db: Session, user_id: int, amount: float, 
                product_name: str, quantity: int = 1,
                unit_price: Optional[float] = None,
                customer_id: Optional[int] = None,
                payment_method: str = "cash",
                notes: Optional[str] = None) -> Sale:
    
    if unit_price is None:
        unit_price = amount / quantity if quantity > 0 else amount
    
    sale = Sale(
        user_id=user_id,
        amount=amount,
        product_name=product_name,
        quantity=quantity,
        unit_price=unit_price,
        customer_id=customer_id,
        payment_method=payment_method,
        notes=notes
    )
    db.add(sale)
    
    # Update customer if exists
    if customer_id:
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.user_id == user_id
        ).first()
        if customer:
            customer.total_purchases += amount
            customer.last_purchase = datetime.now()
    
    db.commit()
    db.refresh(sale)
    return sale

def get_today_sales(db: Session, user_id: int) -> List[Sale]:
    today = date.today()
    return db.query(Sale).filter(
        Sale.user_id == user_id,
        func.date(Sale.sale_date) == today
    ).order_by(desc(Sale.sale_date)).all()

def get_sales_by_date(db: Session, user_id: int, 
                     start_date: date, end_date: date) -> List[Sale]:
    return db.query(Sale).filter(
        Sale.user_id == user_id,
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).order_by(desc(Sale.sale_date)).all()

def get_total_sales(db: Session, user_id: int, 
                   start_date: date, end_date: date) -> float:
    result = db.query(func.sum(Sale.amount)).filter(
        Sale.user_id == user_id,
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).scalar()
    return result or 0.0

# Expense CRUD
def create_expense(db: Session, user_id: int, amount: float,
                   category: str, description: Optional[str] = None) -> Expense:
    expense = Expense(
        user_id=user_id,
        amount=amount,
        category=category,
        description=description
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense

def get_today_expenses(db: Session, user_id: int) -> List[Expense]:
    today = date.today()
    return db.query(Expense).filter(
        Expense.user_id == user_id,
        func.date(Expense.expense_date) == today
    ).order_by(desc(Expense.expense_date)).all()

def get_total_expenses(db: Session, user_id: int,
                      start_date: date, end_date: date) -> float:
    result = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).scalar()
    return result or 0.0

# Product CRUD
def create_product(db: Session, user_id: int, name: str,
                   selling_price: Optional[float] = None,
                   purchase_price: Optional[float] = None,
                   stock: int = 0,
                   category: Optional[str] = None) -> Product:
    product = Product(
        user_id=user_id,
        name=name,
        selling_price=selling_price,
        purchase_price=purchase_price,
        stock=stock,
        category=category
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def get_products(db: Session, user_id: int, 
                active_only: bool = True) -> List[Product]:
    query = db.query(Product).filter(Product.user_id == user_id)
    if active_only:
        query = query.filter(Product.is_active == True)
    return query.order_by(Product.name).all()

def get_product(db: Session, user_id: int, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()

def update_product_stock(db: Session, product_id: int, 
                        quantity: int, operation: str = "add") -> Optional[Product]:
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        if operation == "add":
            product.stock += quantity
        elif operation == "subtract":
            product.stock = max(0, product.stock - quantity)
        elif operation == "set":
            product.stock = max(0, quantity)
        product.updated_at = datetime.now()
        db.commit()
        db.refresh(product)
    return product

# Customer CRUD
def create_customer(db: Session, user_id: int, name: str,
                    phone: Optional[str] = None,
                    email: Optional[str] = None) -> Customer:
    customer = Customer(
        user_id=user_id,
        name=name,
        phone=phone,
        email=email
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

def get_customers(db: Session, user_id: int) -> List[Customer]:
    return db.query(Customer).filter(
        Customer.user_id == user_id
    ).order_by(Customer.name).all()

def get_customer(db: Session, user_id: int, customer_id: int) -> Optional[Customer]:
    return db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.user_id == user_id
    ).first()

def update_customer_credit(db: Session, customer_id: int,
                          amount: float, operation: str = "add") -> Optional[Customer]:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        if operation == "add":
            customer.credit_balance += amount
        elif operation == "subtract":
            customer.credit_balance = max(0, customer.credit_balance - amount)
        elif operation == "set":
            customer.credit_balance = max(0, amount)
        customer.updated_at = datetime.now()
        db.commit()
        db.refresh(customer)
    return customer