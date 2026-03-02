import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy

from config import bot_config
from app.handlers import (
    start, sales, expenses, reports,
    inventory, customers, help, team
)
from app.middlewares.auth import AuthMiddleware
from app.database.connection import init_db
from app.services.notifier import Notifier

async def main():
    """Main function to start the bot"""
    # Initialize database
    await init_db()
    
    # Create bot and dispatcher
    bot = Bot(token=bot_config.TOKEN)
    notifier = Notifier(bot)
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
    dp.include_router(team.router)
    dp.include_router(help.router)
    
    # Start notifier and bot polling
    await notifier.start()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await notifier.stop()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
