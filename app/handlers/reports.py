from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.crud import (
    get_user, get_sales_by_date, get_total_sales,
    get_total_expenses
)
from app.database.connection import get_db_session
from app.services.reports import ReportGenerator
from config import settings
from datetime import datetime, date, timedelta

router = Router()
MENU_BUTTONS = {
    "💰 Record Sale",
    "📊 Today's Report",
    "👥 Customers",
    "🧑‍💼 Team",
    "🚀 Insights",
    "💸 Record Expense",
    "📦 Inventory",
    "❓ Help",
}

class ReportStates(StatesGroup):
    waiting_for_date = State()

@router.message(Command("report"))
async def cmd_report(message: types.Message):
    """Generate daily report"""
    with get_db_session() as db:
        user = get_user(db, message.from_user.id)
        
        if not user:
            await message.answer("❌ Please use /start first.")
            return
        
        # Get today's date
        today = date.today()
        
        # Generate report
        generator = ReportGenerator()
        report = generator.generate_daily_report(db, user.id, today)
        
        await message.answer(report, parse_mode="Markdown")

@router.message(Command("weekly"))
async def cmd_weekly(message: types.Message):
    """Generate weekly report"""
    with get_db_session() as db:
        user = get_user(db, message.from_user.id)
        
        if not user:
            await message.answer("❌ Please use /start first.")
            return
        
        # Calculate week start and end
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday
        
        # Generate report
        generator = ReportGenerator()
        report = generator.generate_weekly_report(db, user.id, week_start, week_end)
        
        await message.answer(report, parse_mode="Markdown")

@router.message(Command("monthly"))
async def cmd_monthly(message: types.Message):
    """Generate monthly report"""
    with get_db_session() as db:
        user = get_user(db, message.from_user.id)
        
        if not user:
            await message.answer("❌ Please use /start first.")
            return
        
        # Calculate month start and end
        today = date.today()
        month_start = date(today.year, today.month, 1)
        if today.month == 12:
            month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        # Generate report
        generator = ReportGenerator()
        report = generator.generate_monthly_report(db, user.id, month_start, month_end)
        
        await message.answer(report, parse_mode="Markdown")

@router.message(Command("profit"))
async def cmd_profit(message: types.Message):
    """Calculate profit for today"""
    with get_db_session() as db:
        user = get_user(db, message.from_user.id)
        
        if not user:
            await message.answer("❌ Please use /start first.")
            return
        
        today = date.today()
        
        # Get totals
        total_sales = get_total_sales(db, user.id, today, today)
        total_expenses = get_total_expenses(db, user.id, today, today)
        profit = total_sales - total_expenses
        
        report = f"💰 *Profit Report - {today.strftime('%d %b %Y')}*\n\n"
        report += f"• Total Sales: {settings.CURRENCY} {total_sales:,.0f}\n"
        report += f"• Total Expenses: {settings.CURRENCY} {total_expenses:,.0f}\n"
        report += f"• Profit: {settings.CURRENCY} {profit:,.0f}\n\n"
        
        if profit > 0:
            report += "📈 Good job! You made a profit today! 🎉"
        elif profit < 0:
            report += "📉 You had a loss today. Review your expenses."
        else:
            report += "📊 You broke even today."
        
        await message.answer(report, parse_mode="Markdown")

@router.message(Command("insights"))
@router.message(lambda message: message.text == "🚀 Insights")
async def cmd_insights(message: types.Message):
    """Generate smart 7-day business insights."""
    with get_db_session() as db:
        user = get_user(db, message.from_user.id)

        if not user:
            await message.answer("❌ Please use /start first.")
            return

        generator = ReportGenerator()
        report = generator.generate_insights_report(db, user.id, days=7)

        await message.answer(report, parse_mode="Markdown")

@router.message(Command("custom_report"))
async def cmd_custom_report(message: types.Message, state: FSMContext):
    """Start custom report generation"""
    with get_db_session() as db:
        user = get_user(db, message.from_user.id)
        
        if not user:
            await message.answer("❌ Please use /start first.")
            return
    
    await message.answer(
        "📅 *Custom Report*\n\n"
        "Enter date range in format:\n"
        "`DD-MM-YYYY to DD-MM-YYYY`\n\n"
        "Example: `01-01-2024 to 31-01-2024`",
        parse_mode="Markdown"
    )
    await state.set_state(ReportStates.waiting_for_date)

@router.message(ReportStates.waiting_for_date)
async def process_custom_date(message: types.Message, state: FSMContext):
    """Process custom date range"""
    if not message.text:
        await message.answer(
            "❌ Invalid date format.\n"
            "Please use: `DD-MM-YYYY to DD-MM-YYYY`",
            parse_mode="Markdown",
        )
        return

    if message.text.startswith("/"):
        await state.clear()
        await message.answer("Custom report input cancelled. Run your command again.")
        return

    if message.text in MENU_BUTTONS:
        await state.clear()
        await message.answer("Custom report input cancelled. Tap the menu option again.")
        return

    text = message.text.strip()
    
    # Parse date range
    try:
        date_parts = text.split(' to ')
        if len(date_parts) != 2:
            raise ValueError
        
        start_date = datetime.strptime(date_parts[0].strip(), "%d-%m-%Y").date()
        end_date = datetime.strptime(date_parts[1].strip(), "%d-%m-%Y").date()
        
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        
        with get_db_session() as db:
            user = get_user(db, message.from_user.id)
            
            # Generate report
            generator = ReportGenerator()
            report = generator.generate_custom_report(
                db, user.id, start_date, end_date
            )
        
        await message.answer(report, parse_mode="Markdown")
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Invalid date format.\n"
            "Please use: `DD-MM-YYYY to DD-MM-YYYY`\n"
            "Example: `01-01-2024 to 31-01-2024`",
            parse_mode="Markdown"
        )
