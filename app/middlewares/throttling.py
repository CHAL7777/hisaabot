from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: int = 1, period: int = 1):
        self.rate_limit = rate_limit
        self.period = period
        self.user_messages = defaultdict(list)
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        # Clean old messages
        now = datetime.now()
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if now - msg_time < timedelta(seconds=self.period)
        ]
        
        # Check rate limit
        if len(self.user_messages[user_id]) >= self.rate_limit:
            # Rate limit exceeded
            if event.text and not event.text.startswith('/'):
                # Don't throttle commands, only regular messages
                await event.answer(
                    "⏳ Please wait a moment before sending another message.",
                    show_alert=False
                )
                return
        
        # Add current message time
        self.user_messages[user_id].append(now)
        
        # Continue processing
        return await handler(event, data)