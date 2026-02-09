import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy

from config import bot_config
from app.handlers import (
    start, sales, expenses, reports,
    inventory, customers, help
)
from app.middlewares.auth import AuthMiddleware
from app.database.connection import init_db

async def main():
    """Main function to start the bot"""
    # Initialize database
    await init_db()
    
    # Create bot and dispatcher
    bot = Bot(token=bot_config.TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.USER_IN_CHAT)
    
    # Register middlewares
    dp.message.middleware(AuthMiddleware())
    
    # Include routers
    dp.include_router(start.router)
    dp.include_router(sales.router)
    dp.include_router(expenses.router)
    dp.include_router(reports.router)
    dp.include_router(inventory.router)
    dp.include_router(customers.router)
    dp.include_router(help.router)
    
    # Start polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())