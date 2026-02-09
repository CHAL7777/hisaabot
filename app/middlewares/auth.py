from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from app.database.crud import get_user, create_user
from app.database.connection import get_db
from config import bot_config

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
        
        # Get user from database
        db = next(get_db())
        user = get_user(db, event.from_user.id)
        
        if not user:
            # User not found, create new user
            user = create_user(
                db=db,
                telegram_id=event.from_user.id,
                full_name=event.from_user.full_name,
                username=event.from_user.username
            )
        
        # Add user to data
        data['user'] = user
        data['db'] = db
        
        # Check if user is admin (for admin-only commands)
        if event.from_user.id in bot_config.ADMIN_IDS:
            data['is_admin'] = True
        else:
            data['is_admin'] = False
        
        return await handler(event, data)