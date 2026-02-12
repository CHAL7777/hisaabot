from datetime import datetime, time, timedelta
from typing import List
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from sqlalchemy.orm import Session

from app.database.crud import get_user, get_today_sales, get_products
from app.database.connection import get_db_session
from config import settings

class Notifier:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
    
    async def start(self):
        """Start the notifier scheduler"""
        # Schedule daily report at 8 PM
        self.scheduler.add_job(
            self.send_daily_reminders,
            CronTrigger(hour=settings.DAILY_REPORT_HOUR, minute=0),
            id="daily_reminder"
        )
        
        # Schedule weekly report on Monday at 9 AM
        self.scheduler.add_job(
            self.send_weekly_report,
            CronTrigger(day_of_week=settings.WEEKLY_REPORT_DAY, hour=9, minute=0),
            id="weekly_report"
        )
        
        # Start scheduler
        self.scheduler.start()
        print(f"Notifier started. Daily reminders at {settings.DAILY_REPORT_HOUR}:00")
    
    async def send_daily_reminders(self):
        """Send daily reminders to all users"""
        with get_db_session() as db:
            # Get all active users
            from app.database.models import User
            users = db.query(User).filter(User.is_active == True).all()
            
            for user in users:
                try:
                    # Check if user recorded sales today
                    sales = get_today_sales(db, user.id)
                    
                    if not sales:
                        # No sales today - send reminder
                        message = (
                            "📝 *Daily Reminder*\n\n"
                            "You haven't recorded any sales today!\n"
                            "Use /sale to record your sales.\n\n"
                            "Every transaction matters for accurate reporting! 💪"
                        )
                        
                        await self.bot.send_message(
                            chat_id=user.telegram_id,
                            text=message,
                            parse_mode="Markdown"
                        )
                    
                    # Check for low stock products
                    products = get_products(db, user.id)
                    low_stock_products = [
                        p for p in products 
                        if p.stock <= p.min_stock and p.stock > 0
                    ]
                    
                    if low_stock_products:
                        message = "⚠️ *Low Stock Alert!*\n\n"
                        for product in low_stock_products[:3]:  # Limit to 3 products
                            message += f"• {product.name}: {product.stock} left (min: {product.min_stock})\n"
                        
                        if len(low_stock_products) > 3:
                            message += f"\n... and {len(low_stock_products) - 3} more products running low."
                        
                        await self.bot.send_message(
                            chat_id=user.telegram_id,
                            text=message,
                            parse_mode="Markdown"
                        )
                        
                except Exception as e:
                    print(f"Error sending reminder to user {user.id}: {e}")
    
    async def send_weekly_report(self):
        """Send weekly report to all users"""
        with get_db_session() as db:
            from app.database.models import User
            users = db.query(User).filter(User.is_active == True).all()
            
            for user in users:
                try:
                    # Calculate week dates
                    today = datetime.now().date()
                    week_start = today - timedelta(days=today.weekday())
                    week_end = week_start + timedelta(days=6)
                    
                    # Get weekly totals (simplified)
                    from app.database.crud import get_total_sales, get_total_expenses
                    total_sales = get_total_sales(db, user.id, week_start, week_end)
                    total_expenses = get_total_expenses(db, user.id, week_start, week_end)
                    profit = total_sales - total_expenses
                    
                    message = (
                        f"📊 *Weekly Report - Week {week_start.strftime('%d %b')} to {week_end.strftime('%d %b')}*\n\n"
                        f"• Total Sales: {settings.CURRENCY} {total_sales:,.0f}\n"
                        f"• Total Expenses: {settings.CURRENCY} {total_expenses:,.0f}\n"
                        f"• Weekly Profit: {settings.CURRENCY} {profit:,.0f}\n\n"
                    )
                    
                    if profit > 0:
                        message += "🌟 *Great week!* Keep up the good work! 🎉"
                    else:
                        message += "💡 *Review your expenses* to improve profitability next week."
                    
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                    
                except Exception as e:
                    print(f"Error sending weekly report to user {user.id}: {e}")
    
    async def stop(self):
        """Stop the notifier"""
        self.scheduler.shutdown()

