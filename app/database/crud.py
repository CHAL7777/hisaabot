from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, date
from typing import List, Optional
import json
from .models import (
    User,
    Sale,
    Expense,
    Product,
    Customer,
    Transaction,
    Business,
    BusinessMember,
    ActivityLog,
)


def _normalize_datetime_range(
    start_date: date | datetime,
    end_date: date | datetime,
) -> tuple[datetime, datetime]:
    """Convert date/datetime inputs to an inclusive datetime range."""
    start_dt = (
        start_date
        if isinstance(start_date, datetime)
        else datetime.combine(start_date, datetime.min.time())
    )
    end_dt = (
        end_date
        if isinstance(end_date, datetime)
        else datetime.combine(end_date, datetime.max.time())
    )
    return start_dt, end_dt


def _scope_user_id(db: Session, user_id: int) -> int:
    """
    Resolve data scope user id.
    For members of a business, all operational data is scoped to the business owner id.
    """
    member = get_active_membership_for_user(db, user_id)
    if not member:
        return user_id

    business = get_business(db, member.business_id)
    if not business:
        return user_id

    return business.owner_user_id

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


# Business + Role CRUD
def create_business(
    db: Session,
    owner_user_id: int,
    name: Optional[str] = None,
    currency: str = "Rp",
    timezone: str = "UTC",
) -> Business:
    business = Business(
        owner_user_id=owner_user_id,
        name=name or "My Business",
        currency=currency,
        timezone=timezone,
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


def get_business(db: Session, business_id: int) -> Optional[Business]:
    return db.query(Business).filter(Business.id == business_id, Business.is_active == True).first()


def get_business_member(
    db: Session,
    business_id: int,
    user_id: int,
    active_only: bool = True,
) -> Optional[BusinessMember]:
    query = db.query(BusinessMember).filter(
        BusinessMember.business_id == business_id,
        BusinessMember.user_id == user_id,
    )
    if active_only:
        query = query.filter(BusinessMember.status == "active")
    return query.first()


def get_active_membership_for_user(db: Session, user_id: int) -> Optional[BusinessMember]:
    return db.query(BusinessMember).filter(
        BusinessMember.user_id == user_id,
        BusinessMember.status == "active",
    ).order_by(BusinessMember.id).first()


def add_or_update_business_member(
    db: Session,
    business_id: int,
    user_id: int,
    role: str,
    status: str = "active",
    invited_by: Optional[int] = None,
) -> BusinessMember:
    member = db.query(BusinessMember).filter(
        BusinessMember.business_id == business_id,
        BusinessMember.user_id == user_id,
    ).first()
    if member:
        member.role = role
        member.status = status
        if invited_by is not None:
            member.invited_by = invited_by
    else:
        member = BusinessMember(
            business_id=business_id,
            user_id=user_id,
            role=role,
            status=status,
            invited_by=invited_by,
        )
        db.add(member)
    db.commit()
    db.refresh(member)
    return member


def get_business_members(db: Session, business_id: int, status: str = "active") -> List[BusinessMember]:
    return db.query(BusinessMember).filter(
        BusinessMember.business_id == business_id,
        BusinessMember.status == status,
    ).order_by(BusinessMember.role, BusinessMember.id).all()


def count_business_owners(db: Session, business_id: int) -> int:
    return db.query(BusinessMember).filter(
        BusinessMember.business_id == business_id,
        BusinessMember.status == "active",
        BusinessMember.role == "owner",
    ).count()


def remove_business_member(db: Session, business_id: int, user_id: int) -> bool:
    member = db.query(BusinessMember).filter(
        BusinessMember.business_id == business_id,
        BusinessMember.user_id == user_id,
        BusinessMember.status == "active",
    ).first()
    if not member:
        return False

    if member.role == "owner" and count_business_owners(db, business_id) <= 1:
        return False

    member.status = "suspended"
    db.commit()
    return True


def ensure_user_business_context(db: Session, user: User) -> tuple[Business, BusinessMember]:
    member = get_active_membership_for_user(db, user.id)
    if member:
        business = get_business(db, member.business_id)
        if business:
            return business, member

    business_name = user.business_name or f"{user.full_name}'s Business"
    business = create_business(
        db=db,
        owner_user_id=user.id,
        name=business_name,
        currency=user.currency or "Rp",
        timezone="UTC",
    )
    member = add_or_update_business_member(
        db=db,
        business_id=business.id,
        user_id=user.id,
        role="owner",
        status="active",
        invited_by=user.id,
    )
    return business, member


def get_or_create_user_by_telegram_id(
    db: Session,
    telegram_id: int,
    full_name: Optional[str] = None,
    username: Optional[str] = None,
) -> User:
    user = get_user(db, telegram_id)
    if user:
        return user
    return create_user(
        db=db,
        telegram_id=telegram_id,
        full_name=full_name or f"User {telegram_id}",
        username=username,
    )


def create_activity_log(
    db: Session,
    business_id: int,
    actor_user_id: int,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    metadata: Optional[dict] = None,
) -> ActivityLog:
    log = ActivityLog(
        business_id=business_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata or {}),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_activity_logs(db: Session, business_id: int, limit: int = 20) -> List[ActivityLog]:
    return db.query(ActivityLog).filter(
        ActivityLog.business_id == business_id
    ).order_by(desc(ActivityLog.created_at)).limit(limit).all()

# Sale CRUD
def create_sale(db: Session, user_id: int, amount: float, 
                product_name: str, quantity: int = 1,
                unit_price: Optional[float] = None,
                customer_id: Optional[int] = None,
                payment_method: str = "cash",
                notes: Optional[str] = None) -> Sale:
    scope_user_id = _scope_user_id(db, user_id)
    
    if unit_price is None:
        unit_price = amount / quantity if quantity > 0 else amount
    
    sale = Sale(
        user_id=scope_user_id,
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
            Customer.user_id == scope_user_id
        ).first()
        if customer:
            customer.total_purchases += amount
            customer.last_purchase = datetime.now()
    
    db.commit()
    db.refresh(sale)
    return sale

def get_today_sales(db: Session, user_id: int) -> List[Sale]:
    today = date.today()
    scope_user_id = _scope_user_id(db, user_id)
    return db.query(Sale).filter(
        Sale.user_id == scope_user_id,
        func.date(Sale.sale_date) == today
    ).order_by(desc(Sale.sale_date)).all()

def get_sales_by_date(db: Session, user_id: int, 
                     start_date: date, end_date: date) -> List[Sale]:
    start_dt, end_dt = _normalize_datetime_range(start_date, end_date)
    scope_user_id = _scope_user_id(db, user_id)
    return db.query(Sale).filter(
        Sale.user_id == scope_user_id,
        Sale.sale_date >= start_dt,
        Sale.sale_date <= end_dt
    ).order_by(desc(Sale.sale_date)).all()

def get_total_sales(db: Session, user_id: int, 
                   start_date: date, end_date: date) -> float:
    start_dt, end_dt = _normalize_datetime_range(start_date, end_date)
    scope_user_id = _scope_user_id(db, user_id)
    result = db.query(func.sum(Sale.amount)).filter(
        Sale.user_id == scope_user_id,
        Sale.sale_date >= start_dt,
        Sale.sale_date <= end_dt
    ).scalar()
    return result or 0.0

# Expense CRUD
def create_expense(db: Session, user_id: int, amount: float,
                   category: str, description: Optional[str] = None) -> Expense:
    scope_user_id = _scope_user_id(db, user_id)
    expense = Expense(
        user_id=scope_user_id,
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
    scope_user_id = _scope_user_id(db, user_id)
    return db.query(Expense).filter(
        Expense.user_id == scope_user_id,
        func.date(Expense.expense_date) == today
    ).order_by(desc(Expense.expense_date)).all()

def get_expenses_by_date(db: Session, user_id: int,
                        start_date: date, end_date: date) -> List[Expense]:
    start_dt, end_dt = _normalize_datetime_range(start_date, end_date)
    scope_user_id = _scope_user_id(db, user_id)
    return db.query(Expense).filter(
        Expense.user_id == scope_user_id,
        Expense.expense_date >= start_dt,
        Expense.expense_date <= end_dt
    ).order_by(desc(Expense.expense_date)).all()

def get_total_expenses(db: Session, user_id: int,
                      start_date: date, end_date: date) -> float:
    start_dt, end_dt = _normalize_datetime_range(start_date, end_date)
    scope_user_id = _scope_user_id(db, user_id)
    result = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == scope_user_id,
        Expense.expense_date >= start_dt,
        Expense.expense_date <= end_dt
    ).scalar()
    return result or 0.0

# Product CRUD
def create_product(db: Session, user_id: int, name: str,
                   selling_price: Optional[float] = None,
                   purchase_price: Optional[float] = None,
                   stock: int = 0,
                   category: Optional[str] = None) -> Product:
    scope_user_id = _scope_user_id(db, user_id)
    product = Product(
        user_id=scope_user_id,
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
    scope_user_id = _scope_user_id(db, user_id)
    query = db.query(Product).filter(Product.user_id == scope_user_id)
    if active_only:
        query = query.filter(Product.is_active == True)
    return query.order_by(Product.name).all()

def get_product(db: Session, user_id: int, product_id: int) -> Optional[Product]:
    scope_user_id = _scope_user_id(db, user_id)
    return db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == scope_user_id
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
    scope_user_id = _scope_user_id(db, user_id)
    customer = Customer(
        user_id=scope_user_id,
        name=name,
        phone=phone,
        email=email
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

def get_customers(db: Session, user_id: int) -> List[Customer]:
    scope_user_id = _scope_user_id(db, user_id)
    return db.query(Customer).filter(
        Customer.user_id == scope_user_id
    ).order_by(Customer.name).all()

def get_customer(db: Session, user_id: int, customer_id: int) -> Optional[Customer]:
    scope_user_id = _scope_user_id(db, user_id)
    return db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.user_id == scope_user_id
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
