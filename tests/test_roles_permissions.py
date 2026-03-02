from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.crud import (
    create_user,
    ensure_user_business_context,
    get_business_members,
    add_or_update_business_member,
    remove_business_member,
    create_sale,
    get_total_sales,
)
from app.database.models import Base
from app.services.permissions import resolve_action_from_text, has_permission


def _build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_business_context_bootstrap_creates_owner_membership():
    db = _build_session()
    user = create_user(db, telegram_id=1001, full_name="Owner One")

    business, member = ensure_user_business_context(db, user)
    members = get_business_members(db, business.id)

    assert business.owner_user_id == user.id
    assert member.role == "owner"
    assert len(members) == 1


def test_cannot_remove_last_owner():
    db = _build_session()
    owner = create_user(db, telegram_id=2001, full_name="Owner One")
    business, _ = ensure_user_business_context(db, owner)

    ok = remove_business_member(db, business.id, owner.id)
    assert ok is False


def test_can_remove_non_owner_member():
    db = _build_session()
    owner = create_user(db, telegram_id=3001, full_name="Owner One")
    staff = create_user(db, telegram_id=3002, full_name="Staff User")

    business, _ = ensure_user_business_context(db, owner)
    add_or_update_business_member(
        db=db,
        business_id=business.id,
        user_id=staff.id,
        role="staff",
        status="active",
        invited_by=owner.id,
    )

    ok = remove_business_member(db, business.id, staff.id)
    assert ok is True


def test_permission_resolution_and_checks():
    assert resolve_action_from_text("/sale 500 bread") == "sale:create"
    assert resolve_action_from_text("📦 Inventory") == "inventory:view"
    assert resolve_action_from_text("🧑‍💼 Team") == "member:view"
    assert has_permission("staff", "sale:create") is True
    assert has_permission("staff", "report:view") is False
    assert has_permission("manager", "report:view") is True


def test_member_sales_are_scoped_to_business_owner_data():
    db = _build_session()
    owner = create_user(db, telegram_id=4001, full_name="Owner One")
    staff = create_user(db, telegram_id=4002, full_name="Staff User")
    business, _ = ensure_user_business_context(db, owner)
    add_or_update_business_member(
        db=db,
        business_id=business.id,
        user_id=staff.id,
        role="staff",
        status="active",
        invited_by=owner.id,
    )

    create_sale(
        db=db,
        user_id=staff.id,
        amount=1000,
        product_name="Bread",
        quantity=1,
    )

    assert get_total_sales(db, owner.id, date.today(), date.today()) == 1000
