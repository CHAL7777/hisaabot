#!/usr/bin/env python3
"""
Script to generate and send daily reports.
Can be run manually or via cron job.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from app.database.connection import get_db, engine
from app.database.crud import get_user
from app.services.reports import ReportGenerator
from config import bot_config
import asyncio
from aiogram import Bot

async def send_daily_reports():
    """Send daily reports to all users"""
    bot = Bot(token=bot_config.TOKEN)
    db = next(get_db())
    generator = ReportGenerator()
    
    # Get all active users
    from app.database.models import User
    users = db.query(User).filter(User.is_active == True).all()
    
    yesterday = date.today() - timedelta(days=1)
    
    for user in users:
        try:
            report = generator.generate_daily_report(db, user.id, yesterday)
            
            await bot.send_message(
                chat_id=user.telegram_id,
                text=f"📊 *Yesterday's Report ({yesterday.strftime('%d %b %Y')})*\n\n{report}",
                parse_mode="Markdown"
            )
            
            print(f"Sent report to user {user.telegram_id}")
            
        except Exception as e:
            print(f"Error sending report to user {user.telegram_id}: {e}")
    
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(send_daily_reports())