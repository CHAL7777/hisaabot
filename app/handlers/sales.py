from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.crud import get_user, create_sale, get_today_sales
from app.database.connection import get_db
from app.services.parser import Parser
from app.services.calculator import Calculator
from config import messages, settings
from datetime import datetime
import re

router = Router()

class SaleStates(StatesGroup):
    waiting_for_sale = State()
    waiting_for_quantity = State()

@router.message(Command("sale"))
@router.message(F.text.regexp(r'^💰 Record Sale$'))
async def cmd_sale(message: types.Message, state: FSMContext):
    """Handle /sale command"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    if not user:
        await message.answer("❌ Please use /start first.")
        return
    
    await message.answer(
        "💵 *Record a Sale*\n\n"
        "Enter sale details in one of these formats:\n"
        "• `500 bread` - Single item\n"
        "• `3x 500 bread` - Multiple items\n"
        "• `500 bread 3` - With quantity at end\n\n"
        "Or enter just the amount to add details later.",
        parse_mode="Markdown"
    )
    await state.set_state(SaleStates.waiting_for_sale)

@router.message(SaleStates.waiting_for_sale)
async def process_sale(message: types.Message, state: FSMContext):
    """Process sale input"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    text = message.text.strip()
    
    # Try to parse with parser
    parser = Parser()
    parsed_sale = parser.parse_sale(text)
    
    if parsed_sale:
        # Create sale with parsed data
        sale = create_sale(
            db=db,
            user_id=user.id,
            amount=parsed_sale.amount,
            product_name=parsed_sale.item,
            quantity=parsed_sale.quantity,
            unit_price=parsed_sale.amount / parsed_sale.quantity
        )
        
        await message.answer(
            f"✅ Sale recorded!\n"
            f"• Amount: {settings.CURRENCY} {parsed_sale.amount:,.0f}\n"
            f"• Item: {parsed_sale.item}\n"
            f"• Quantity: {parsed_sale.quantity}\n"
            f"• Time: {datetime.now().strftime('%H:%M')}",
            parse_mode="Markdown"
        )
        await state.clear()
    
    elif text.replace('.', '').isdigit():
        # Only amount provided, ask for product
        amount = float(text)
        await state.update_data(amount=amount)
        await message.answer(
            f"Amount: {settings.CURRENCY} {amount:,.0f}\n"
            "Now enter product name:"
        )
        await state.set_state(SaleStates.waiting_for_quantity)
    
    else:
        await message.answer(
            "❌ I couldn't understand that format.\n"
            "Please use: `500 bread` or `3x 500 bread`",
            parse_mode="Markdown"
        )

@router.message(SaleStates.waiting_for_quantity)
async def process_product_name(message: types.Message, state: FSMContext):
    """Process product name after amount"""
    data = await state.get_data()
    amount = data.get('amount', 0)
    product_name = message.text.strip()
    
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    sale = create_sale(
        db=db,
        user_id=user.id,
        amount=amount,
        product_name=product_name,
        quantity=1,
        unit_price=amount
    )
    
    await message.answer(
        f"✅ Sale recorded!\n"
        f"• Amount: {settings.CURRENCY} {amount:,.0f}\n"
        f"• Product: {product_name}\n"
        f"• Time: {datetime.now().strftime('%H:%M')}",
        parse_mode="Markdown"
    )
    await state.clear()

@router.message(Command("today"))
@router.message(F.text.regexp(r'^📊 Today\'s Report$'))
async def cmd_today(message: types.Message):
    """Show today's sales summary"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    if not user:
        await message.answer("❌ Please use /start first.")
        return
    
    # Get today's sales and expenses
    sales = get_today_sales(db, user.id)
    
    if not sales:
        await message.answer("📭 No sales recorded today.")
        return
    
    # Calculate totals
    calculator = Calculator()
    total_sales = calculator.calculate_total(sales)
    
    # Format message
    report = f"📊 *Today's Sales Report*\n"
    report += f"• Total Sales: {settings.CURRENCY} {total_sales:,.0f}\n"
    report += f"• Number of Sales: {len(sales)}\n\n"
    report += "*Recent Sales:*\n"
    
    for sale in sales[:5]:  # Show last 5 sales
        time_str = sale.sale_date.strftime("%H:%M")
        report += f"• {time_str} - {settings.CURRENCY} {sale.amount:,.0f}"
        if sale.product_name:
            report += f" ({sale.product_name})"
        report += "\n"
    
    if len(sales) > 5:
        report += f"\n... and {len(sales) - 5} more sales"
    
    await message.answer(report, parse_mode="Markdown")