from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from app.database.crud import (
    get_user,
    create_user,
    ensure_user_business_context,
    create_activity_log,
)
from app.database.connection import SessionLocal
from config import bot_config
from app.services.permissions import resolve_action_from_text, has_permission, action_label

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Skip auth for /start command
        if isinstance(event, Message) and event.text and event.text.startswith('/start'):
            return await handler(event, data)
        
        # Create a new database session directly
        db = SessionLocal()
        try:
            user = get_user(db, event.from_user.id)
            
            if not user:
                # User not found, create new user
                user = create_user(
                    db=db,
                    telegram_id=event.from_user.id,
                    full_name=event.from_user.full_name,
                    username=event.from_user.username
                )
            
            # Add user and db session to data for handlers to reuse
            data['user'] = user
            data['db'] = db
            business, membership = ensure_user_business_context(db, user)
            data['business'] = business
            data['membership'] = membership
            data['role'] = membership.role
        
        except Exception:
            # Close db on error
            db.close()
            raise
        
        # Check if user is admin (for admin-only commands)
        if event.from_user.id in bot_config.ADMIN_IDS:
            data['is_admin'] = True
        else:
            data['is_admin'] = False

        action = None
        if isinstance(event, Message):
            action = resolve_action_from_text(event.text)
            role = data.get("role", "staff")
            if not has_permission(role, action):
                await event.answer(
                    f"❌ Permission denied. Your role ({role}) cannot perform {action_label(action)}."
                )
                return
        
        try:
            result = await handler(event, data)
            if action and data.get("business"):
                log_db = SessionLocal()
                try:
                    create_activity_log(
                        db=log_db,
                        business_id=data["business"].id,
                        actor_user_id=user.id,
                        action=action,
                        entity_type="command",
                        metadata={"text": event.text[:200] if isinstance(event, Message) and event.text else ""},
                    )
                finally:
                    log_db.close()
        finally:
            # Close the session after handler completes
            db.close()
        
        return result
