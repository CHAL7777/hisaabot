from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.crud import get_sales_by_date, get_total_expenses, get_total_sales
from app.database.models import Base, Expense, Sale


def _build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_same_day_sales_are_included_in_totals_and_list():
    db = _build_session()
    db.add(Sale(user_id=1, amount=1200, product_name="bread"))
    db.commit()

    today = date.today()
    assert get_total_sales(db, 1, today, today) == 1200
    assert len(get_sales_by_date(db, 1, today, today)) == 1


def test_same_day_expenses_are_included_in_totals():
    db = _build_session()
    db.add(Expense(user_id=1, amount=300, category="supplies"))
    db.commit()

    today = date.today()
    assert get_total_expenses(db, 1, today, today) == 300
