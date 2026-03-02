from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.database.crud import (
    get_or_create_user_by_telegram_id,
    add_or_update_business_member,
    get_business_members,
    get_user,
    remove_business_member,
    count_business_owners,
    get_activity_logs,
)
from app.database.models import User, BusinessMember
from app.services.permissions import has_permission

router = Router()

TEAM_PANEL_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="team:refresh"),
            InlineKeyboardButton(text="📜 Recent Activity", callback_data="team:activity"),
        ],
        [InlineKeyboardButton(text="❓ How To Use", callback_data="team:help")],
    ]
)

TEAM_BACK_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Back To Team", callback_data="team:back")]
    ]
)


def _build_team_summary(db, business) -> str:
    members = get_business_members(db, business.id, status="active")
    if not members:
        return f"Team - {business.name}\n\nNo active members found."

    user_ids = [member.user_id for member in members]
    user_map = {
        user.id: user
        for user in db.query(User).filter(User.id.in_(user_ids)).all()
    }

    role_icon = {"owner": "👑", "manager": "🧑‍💼", "staff": "🛠"}
    response = f"Team - {business.name}\n\n"
    for member in members:
        member_user = user_map.get(member.user_id)
        display = member_user.full_name if member_user else f"User {member.user_id}"
        icon = role_icon.get(member.role, "•")
        response += f"{icon} {display} [{member.role}]\n"

    response += "\nQuick commands:\n"
    response += "/invite <telegram_id> <owner|manager|staff>\n"
    response += "/set_role <telegram_id> <owner|manager|staff>\n"
    response += "/remove_member <telegram_id>"
    return response


def _build_activity_summary(db, business, limit: int = 10) -> str:
    logs = get_activity_logs(db, business.id, limit=limit)
    if not logs:
        return "Recent Activity\n\nNo activity logs yet."

    actor_ids = list({log.actor_user_id for log in logs})
    actor_map = {
        user.id: user
        for user in db.query(User).filter(User.id.in_(actor_ids)).all()
    }

    response = f"Recent Activity (last {len(logs)})\n\n"
    for log in logs:
        actor = actor_map.get(log.actor_user_id)
        actor_name = actor.full_name if actor else f"User {log.actor_user_id}"
        timestamp = log.created_at.strftime("%d %b %H:%M")
        response += f"• {timestamp} - {actor_name}: {log.action}\n"
    return response


async def _edit_or_send(callback: types.CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup):
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text, reply_markup=reply_markup)


@router.message(Command("team"))
@router.message(lambda message: message.text == "🧑‍💼 Team")
async def cmd_team(message: types.Message, db=None, business=None, role=None):
    """Show interactive team panel."""
    if db is None or business is None:
        await message.answer("❌ Team context is unavailable. Try /start again.")
        return

    if not has_permission(role or "staff", "member:view"):
        await message.answer("❌ Permission denied. Only owner/manager can view team panel.")
        return

    await message.answer(
        _build_team_summary(db, business),
        reply_markup=TEAM_PANEL_KEYBOARD,
    )


@router.callback_query(F.data == "team:refresh")
async def cb_team_refresh(callback: types.CallbackQuery, db=None, business=None, role=None):
    if db is None or business is None:
        await callback.answer("Team context unavailable.", show_alert=True)
        return
    if not has_permission(role or "staff", "member:view"):
        await callback.answer("Permission denied.", show_alert=True)
        return

    await _edit_or_send(callback, _build_team_summary(db, business), TEAM_PANEL_KEYBOARD)
    await callback.answer("Refreshed.")


@router.callback_query(F.data == "team:activity")
async def cb_team_activity(callback: types.CallbackQuery, db=None, business=None, role=None):
    if db is None or business is None:
        await callback.answer("Team context unavailable.", show_alert=True)
        return
    if not has_permission(role or "staff", "activity:view"):
        await callback.answer("Permission denied.", show_alert=True)
        return

    await _edit_or_send(callback, _build_activity_summary(db, business), TEAM_BACK_KEYBOARD)
    await callback.answer()


@router.callback_query(F.data == "team:help")
async def cb_team_help(callback: types.CallbackQuery, role=None):
    if not has_permission(role or "staff", "member:view"):
        await callback.answer("Permission denied.", show_alert=True)
        return

    help_text = (
        "Team Panel Help\n\n"
        "1. Add member:\n"
        "/invite <telegram_id> <owner|manager|staff>\n\n"
        "2. Change role:\n"
        "/set_role <telegram_id> <owner|manager|staff>\n\n"
        "3. Remove member:\n"
        "/remove_member <telegram_id>\n\n"
        "Note: Last owner protection is enabled."
    )
    await _edit_or_send(callback, help_text, TEAM_BACK_KEYBOARD)
    await callback.answer()


@router.callback_query(F.data == "team:back")
async def cb_team_back(callback: types.CallbackQuery, db=None, business=None, role=None):
    if db is None or business is None:
        await callback.answer("Team context unavailable.", show_alert=True)
        return
    if not has_permission(role or "staff", "member:view"):
        await callback.answer("Permission denied.", show_alert=True)
        return

    await _edit_or_send(callback, _build_team_summary(db, business), TEAM_PANEL_KEYBOARD)
    await callback.answer()


@router.message(Command("invite"))
async def cmd_invite(message: types.Message, db=None, business=None, user=None):
    """Invite or add a member to business."""
    if db is None or business is None or user is None:
        await message.answer("❌ Team context is unavailable. Try /start again.")
        return

    args = (message.text or "").split()
    if len(args) != 3:
        await message.answer("Usage: /invite <telegram_id> <owner|manager|staff>")
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ telegram_id must be a number.")
        return

    role = args[2].lower()
    if role not in {"owner", "manager", "staff"}:
        await message.answer("❌ Role must be one of: owner, manager, staff.")
        return

    target_user = get_or_create_user_by_telegram_id(
        db=db,
        telegram_id=telegram_id,
        full_name=f"User {telegram_id}",
    )

    member = add_or_update_business_member(
        db=db,
        business_id=business.id,
        user_id=target_user.id,
        role=role,
        status="active",
        invited_by=user.id,
    )

    await message.answer(
        f"✅ Member added/updated.\n"
        f"• Telegram ID: {telegram_id}\n"
        f"• Role: {member.role}",
        reply_markup=TEAM_PANEL_KEYBOARD,
    )


@router.message(Command("set_role"))
async def cmd_set_role(message: types.Message, db=None, business=None):
    """Update member role."""
    if db is None or business is None:
        await message.answer("❌ Team context is unavailable. Try /start again.")
        return

    args = (message.text or "").split()
    if len(args) != 3:
        await message.answer("Usage: /set_role <telegram_id> <owner|manager|staff>")
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ telegram_id must be a number.")
        return

    role = args[2].lower()
    if role not in {"owner", "manager", "staff"}:
        await message.answer("❌ Role must be one of: owner, manager, staff.")
        return

    target_user = get_user(db, telegram_id)
    if not target_user:
        await message.answer("❌ User not found.")
        return

    existing = db.query(BusinessMember).filter(
        BusinessMember.business_id == business.id,
        BusinessMember.user_id == target_user.id,
        BusinessMember.status == "active",
    ).first()
    if not existing:
        await message.answer("❌ User is not an active member of this business.")
        return

    if existing.role == "owner" and role != "owner" and count_business_owners(db, business.id) <= 1:
        await message.answer("❌ Cannot demote the last owner.")
        return

    existing.role = role
    db.commit()

    await message.answer(
        f"✅ Role updated for {telegram_id}: {role}",
        reply_markup=TEAM_PANEL_KEYBOARD,
    )


@router.message(Command("remove_member"))
async def cmd_remove_member(message: types.Message, db=None, business=None):
    """Suspend active membership."""
    if db is None or business is None:
        await message.answer("❌ Team context is unavailable. Try /start again.")
        return

    args = (message.text or "").split()
    if len(args) != 2:
        await message.answer("Usage: /remove_member <telegram_id>")
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ telegram_id must be a number.")
        return

    target_user = get_user(db, telegram_id)
    if not target_user:
        await message.answer("❌ User not found.")
        return

    ok = remove_business_member(db, business.id, target_user.id)
    if not ok:
        await message.answer("❌ Could not remove member (member missing or last owner protection).")
        return

    await message.answer(
        f"✅ Member removed: {telegram_id}",
        reply_markup=TEAM_PANEL_KEYBOARD,
    )


@router.message(Command("activity"))
async def cmd_activity(message: types.Message, db=None, business=None):
    """Show recent activity logs."""
    if db is None or business is None:
        await message.answer("❌ Team context is unavailable. Try /start again.")
        return

    args = (message.text or "").split()
    limit = 15
    if len(args) > 1:
        try:
            limit = max(1, min(50, int(args[1])))
        except ValueError:
            await message.answer("❌ Limit must be a number between 1 and 50.")
            return

    await message.answer(
        _build_activity_summary(db, business, limit=limit),
        reply_markup=TEAM_BACK_KEYBOARD,
    )
