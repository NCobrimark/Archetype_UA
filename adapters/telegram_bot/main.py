# Bot Version: 1.0.9 - Fix Crash & AI Fallback Enabled
import asyncio
import logging
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Fix path to allow importing from root if running as script
import os
sys.path.append(os.getcwd())

from core.config import settings
from adapters.db_repo import db_repo
from adapters.telegram_bot.handlers import router as bot_router

async def main():
    # Logging config
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Init DB
    await db_repo.init_db()

    # Load .env explicitly (just in case)
    from dotenv import load_dotenv
    load_dotenv()
    
    # Init Bot
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register Routers
    dp.include_router(bot_router)
    
    # Start Polling
    try:
        logging.info("Starting Bot Polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
