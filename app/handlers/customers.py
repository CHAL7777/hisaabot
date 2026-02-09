from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.crud import (
    get_user, create_customer, get_customers,
    get_customer, update_customer_credit
)
from app.database.connection import get_db
from config import messages, settings
from datetime import datetime

router = Router()

class CustomerStates(StatesGroup):
    waiting_for_customer = State()
    waiting_for_credit = State()

@router.message(Command("add_customer"))
async def cmd_add_customer(message: types.Message, state: FSMContext):
    """Add a new customer"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    if not user:
        await message.answer("❌ Please use /start first.")
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) > 1:
        # Parse arguments: /add_customer name phone
        try:
            name = args[1]
            phone = args[2] if len(args) > 2 else None
            
            customer = create_customer(
                db=db,
                user_id=user.id,
                name=name,
                phone=phone
            )
            
            await message.answer(
                f"✅ Customer added!\n"
                f"• Name: {customer.name}\n"
                f"• Phone: {customer.phone or 'N/A'}\n"
                f"• Credit Limit: {settings.CURRENCY} {customer.credit_limit:,.0f}",
                parse_mode="Markdown"
            )
            return
            
        except (ValueError, IndexError):
            pass  # Fall through to interactive mode
    
    await message.answer(
        "👥 *Add New Customer*\n\n"
        "Enter customer details in format:\n"
        "`Name Phone`\n\n"
        "Example: `John Doe +62123456789`\n"
        "You can also enter just the name.",
        parse_mode="Markdown"
    )
    await state.set_state(CustomerStates.waiting_for_customer)

@router.message(CustomerStates.waiting_for_customer)
async def process_customer_input(message: types.Message, state: FSMContext):
    """Process customer input"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    text = message.text.strip()
    parts = text.split(maxsplit=1)
    
    if len(parts) == 2:
        name, phone = parts
    else:
        name = text
        phone = None
    
    customer = create_customer(
        db=db,
        user_id=user.id,
        name=name,
        phone=phone
    )
    
    response = f"✅ Customer added!\n• Name: {customer.name}"
    if customer.phone:
        response += f"\n• Phone: {customer.phone}"
    response += f"\n• Customer ID: {customer.id}"
    
    await message.answer(response, parse_mode="Markdown")
    await state.clear()

@router.message(Command("customers"))
@router.message(F.text.regexp(r'^👥 Customers$'))
async def cmd_customers(message: types.Message):
    """List all customers"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    if not user:
        await message.answer("❌ Please use /start first.")
        return
    
    customers = get_customers(db, user.id)
    
    if not customers:
        await message.answer("📭 No customers yet. Use /add_customer to add one.")
        return
    
    # Separate customers with credit and without
    with_credit = [c for c in customers if c.credit_balance > 0]
    without_credit = [c for c in customers if c.credit_balance == 0]
    
    response = f"👥 *Customers - {len(customers)} Total*\n\n"
    
    if with_credit:
        response += "💰 *Customers with Credit:*\n"
        total_credit = 0
        for customer in with_credit[:5]:  # Limit to first 5
            response += f"• {customer.name}: {settings.CURRENCY} {customer.credit_balance:,.0f}"
            if customer.phone:
                response += f" ({customer.phone})"
            response += "\n"
            total_credit += customer.credit_balance
        
        response += f"\n*Total Credit Outstanding:* {settings.CURRENCY} {total_credit:,.0f}\n\n"
    
    response += "*All Customers:*\n"
    for customer in without_credit[:10]:  # Limit to first 10
        response += f"• {customer.name}"
        if customer.phone:
            response += f" ({customer.phone})"
        if customer.total_purchases > 0:
            response += f" - Spent: {settings.CURRENCY} {customer.total_purchases:,.0f}"
        response += "\n"
    
    if len(customers) > 10:
        response += f"\n... and {len(customers) - 10} more customers"
    
    await message.answer(response, parse_mode="Markdown")

@router.message(Command("credit"))
async def cmd_credit(message: types.Message, state: FSMContext):
    """Add credit to customer"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    if not user:
        await message.answer("❌ Please use /start first.")
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "💰 *Add Customer Credit*\n\n"
            "Usage: /credit [customer] [amount]\n"
            "Example: /credit John 50000\n\n"
            "To give credit (customer owes you): positive amount\n"
            "To record payment (customer paid): negative amount\n"
            "Example: /credit John -50000 (for payment)",
            parse_mode="Markdown"
        )
        return
    
    customer_name = args[1]
    try:
        amount = float(args[2])
    except ValueError:
        await message.answer("❌ Amount must be a number")
        return
    
    # Find customer
    customers = get_customers(db, user.id)
    customer = next((c for c in customers if customer_name.lower() in c.name.lower()), None)
    
    if not customer:
        await message.answer(f"❌ Customer '{customer_name}' not found")
        return
    
    # Update credit
    operation = "add" if amount >= 0 else "subtract"
    amount_abs = abs(amount)
    updated = update_customer_credit(db, customer.id, amount_abs, operation)
    
    if updated:
        action = "added" if amount >= 0 else "deducted"
        await message.answer(
            f"✅ Credit {action}!\n"
            f"• Customer: {updated.name}\n"
            f"• Amount: {settings.CURRENCY} {amount_abs:,.0f}\n"
            f"• New Balance: {settings.CURRENCY} {updated.credit_balance:,.0f}"
        )
    else:
        await message.answer("❌ Failed to update credit")

@router.message(Command("credits"))
async def cmd_credits(message: types.Message):
    """Show all customers with credit"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    if not user:
        await message.answer("❌ Please use /start first.")
        return
    
    customers = get_customers(db, user.id)
    credit_customers = [c for c in customers if c.credit_balance > 0]
    
    if not credit_customers:
        await message.answer("✅ No customers have outstanding credit.")
        return
    
    total_credit = sum(c.credit_balance for c in credit_customers)
    
    response = f"💰 *Outstanding Credit - {settings.CURRENCY} {total_credit:,.0f}*\n\n"
    
    for customer in credit_customers:
        response += f"• *{customer.name}*: {settings.CURRENCY} {customer.credit_balance:,.0f}"
        if customer.phone:
            response += f" 📞 {customer.phone}"
        if customer.last_purchase:
            last_purchase = customer.last_purchase.strftime("%d %b")
            response += f" (Last: {last_purchase})"
        response += "\n"
    
    response += "\n💡 *Tip:* Use /credit [customer] -[amount] to record payments."
    
    await message.answer(response, parse_mode="Markdown")