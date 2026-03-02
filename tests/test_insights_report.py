from datetime import date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Customer, Expense, Product, Sale
from app.services.reports import ReportGenerator


def _build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_generate_insights_report_with_data():
    db = _build_session()
    today = date.today()

    db.add_all(
        [
            Sale(
                user_id=1,
                amount=1000,
                product_name="Bread",
                sale_date=datetime.combine(today - timedelta(days=1), datetime.min.time()),
            ),
            Sale(
                user_id=1,
                amount=400,
                product_name="Milk",
                sale_date=datetime.combine(today - timedelta(days=2), datetime.min.time()),
            ),
            Sale(
                user_id=1,
                amount=500,
                product_name="Bread",
                sale_date=datetime.combine(today - timedelta(days=10), datetime.min.time()),
            ),
            Expense(
                user_id=1,
                amount=300,
                category="rent",
                expense_date=datetime.combine(today - timedelta(days=1), datetime.min.time()),
            ),
            Expense(
                user_id=1,
                amount=100,
                category="rent",
                expense_date=datetime.combine(today - timedelta(days=10), datetime.min.time()),
            ),
            Product(user_id=1, name="Bread", stock=2, min_stock=5),
            Customer(user_id=1, name="John", credit_balance=250),
        ]
    )
    db.commit()

    report = ReportGenerator().generate_insights_report(db, user_id=1, days=7)

    assert "Business Insights (7 Days)" in report
    assert "Top Product: Bread" in report
    assert "Biggest Expense: Rent" in report
    assert "Outstanding Credit" in report
    assert "Low Stock Items: 1" in report
    assert "Recommendations" in report


def test_generate_insights_report_without_data():
    db = _build_session()

    report = ReportGenerator().generate_insights_report(db, user_id=1, days=7)

    assert "Business Insights (7 Days)" in report
    assert "Top Product: No sales data yet" in report
    assert "Biggest Expense: No expense data yet" in report
    assert "Record at least one sale daily" in report
