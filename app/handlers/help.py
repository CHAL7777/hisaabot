from aiogram import Router, types
from aiogram.filters import Command
from config import messages

router = Router()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Show help message"""
    await message.answer(
        messages.HELP,
        parse_mode="Markdown"
    )

@router.message(Command("commands"))
async def cmd_commands(message: types.Message):
    """List all commands"""
    await message.answer(
        messages.HELP,
        parse_mode="Markdown"
    )

