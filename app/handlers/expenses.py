from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.crud import get_user, create_expense, get_today_expenses
from app.database.connection import get_db
from app.services.parser import Parser
from config import messages, settings
from datetime import datetime

router = Router()

class ExpenseStates(StatesGroup):
    waiting_for_expense = State()
    waiting_for_category = State()

@router.message(Command("expense"))
@router.message(F.text.regexp(r'^💸 Record Expense$'))
async def cmd_expense(message: types.Message, state: FSMContext):
    """Handle /expense command"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    if not user:
        await message.answer("❌ Please use /start first.")
        return
    
    await message.answer(
        "💸 *Record an Expense*\n\n"
        "Enter expense details:\n"
        "• `500 supplies` - With category\n"
        "• Or just the amount to select category later\n\n"
        "*Common categories:* supplies, rent, salary, transport, utilities",
        parse_mode="Markdown"
    )
    await state.set_state(ExpenseStates.waiting_for_expense)

@router.message(ExpenseStates.waiting_for_expense)
async def process_expense(message: types.Message, state: FSMContext):
    """Process expense input"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    text = message.text.strip()
    
    # Try to parse with parser
    parser = Parser()
    amount, category = parser.parse_expense(text)
    
    if amount is not None:
        if category:
            # Create expense with both amount and category
            expense = create_expense(
                db=db,
                user_id=user.id,
                amount=amount,
                category=category.lower(),
                description=text
            )
            
            await message.answer(
                f"✅ Expense recorded!\n"
                f"• Amount: {settings.CURRENCY} {amount:,.0f}\n"
                f"• Category: {category}\n"
                f"• Time: {datetime.now().strftime('%H:%M')}",
                parse_mode="Markdown"
            )
            await state.clear()
        else:
            # Only amount provided, ask for category
            await state.update_data(amount=amount)
            await message.answer(
                f"Amount: {settings.CURRENCY} {amount:,.0f}\n"
                "Enter expense category:\n"
                "(supplies, rent, salary, transport, utilities, or custom)",
                parse_mode="Markdown"
            )
            await state.set_state(ExpenseStates.waiting_for_category)
    
    elif text.replace('.', '').isdigit():
        # Only number provided
        amount = float(text)
        await state.update_data(amount=amount)
        await message.answer(
            f"Amount: {settings.CURRENCY} {amount:,.0f}\n"
            "Enter expense category:\n"
            "(supplies, rent, salary, transport, utilities, or custom)",
            parse_mode="Markdown"
        )
        await state.set_state(ExpenseStates.waiting_for_category)
    
    else:
        await message.answer(
            "❌ Please enter amount and category.\n"
            "Example: `500 supplies`",
            parse_mode="Markdown"
        )

@router.message(ExpenseStates.waiting_for_category)
async def process_expense_category(message: types.Message, state: FSMContext):
    """Process expense category"""
    data = await state.get_data()
    amount = data.get('amount', 0)
    category = message.text.strip().lower()
    
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    expense = create_expense(
        db=db,
        user_id=user.id,
        amount=amount,
        category=category,
        description=f"{category} expense"
    )
    
    await message.answer(
        f"✅ Expense recorded!\n"
        f"• Amount: {settings.CURRENCY} {amount:,.0f}\n"
        f"• Category: {category}\n"
        f"• Time: {datetime.now().strftime('%H:%M')}",
        parse_mode="Markdown"
    )
    await state.clear()

@router.message(Command("expenses_today"))
async def cmd_expenses_today(message: types.Message):
    """Show today's expenses"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    if not user:
        await message.answer("❌ Please use /start first.")
        return
    
    expenses = get_today_expenses(db, user.id)
    
    if not expenses:
        await message.answer("📭 No expenses recorded today.")
        return
    
    total = sum(exp.amount for exp in expenses)
    
    report = f"💸 *Today's Expenses*\n"
    report += f"• Total: {settings.CURRENCY} {total:,.0f}\n"
    report += f"• Count: {len(expenses)}\n\n"
    report += "*Details:*\n"
    
    # Group by category
    categories = {}
    for exp in expenses:
        categories[exp.category] = categories.get(exp.category, 0) + exp.amount
    
    for category, amount in categories.items():
        report += f"• {category.title()}: {settings.CURRENCY} {amount:,.0f}\n"
    
    await message.answer(report, parse_mode="Markdown")