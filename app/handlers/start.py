from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.database.crud import get_user, create_user
from app.database.connection import get_db
from config import messages

router = Router()

# Create keyboard
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="💰 Record Sale"),
            KeyboardButton(text="💸 Record Expense")
        ],
        [
            KeyboardButton(text="📊 Today's Report"),
            KeyboardButton(text="📦 Inventory")
        ],
        [
            KeyboardButton(text="👥 Customers"),
            KeyboardButton(text="❓ Help")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    db = next(get_db())
    
    # Check if user exists
    user = get_user(db, message.from_user.id)
    if not user:
        # Create new user
        user = create_user(
            db=db,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )
        welcome_msg = f"🎉 Welcome to MicroBiz Bot, {message.from_user.full_name}!\n\n{messages.WELCOME}"
    else:
        welcome_msg = f"👋 Welcome back, {user.full_name}!\n\nUse /help to see available commands."
    
    await message.answer(
        welcome_msg,
        reply_markup=main_keyboard,
        parse_mode="Markdown"
    )

@router.message(lambda message: message.text == "❓ Help")
async def help_button(message: types.Message):
    """Handle help button"""
    await message.answer(messages.HELP, parse_mode="Markdown")

@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    """Handle /settings command"""
    db = next(get_db())
    user = get_user(db, message.from_user.id)
    
    if not user:
        await message.answer("❌ Please use /start first.")
        return
    
    settings_text = f"""
⚙️ *Your Settings:*

*Business Info:*
• Name: {user.business_name or 'Not set'}
• Currency: {user.currency}
• Language: {user.language}

*To update settings, use:*
/set_business [name] - Set business name
/set_currency [code] - Set currency (Rp, $, €)
/set_language [en/id] - Set language

*Other commands:*
/reset_data - Reset all data (careful!)
/export_data - Export data as CSV
"""
    
    await message.answer(settings_text, parse_mode="Markdown")