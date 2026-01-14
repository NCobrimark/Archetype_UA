import asyncio
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
    
    # Init Bot
    # DEBUGGING: Print Env Vars (Safe)
    logging.info(f"DEBUG: Environment Keys: {[k for k in os.environ.keys() if 'TOKEN' in k or 'KEY' in k]}")
    raw_token = os.environ.get("BOT_TOKEN")
    logging.info(f"DEBUG: Raw os.environ['BOT_TOKEN'] type: {type(raw_token)}, length: {len(raw_token) if raw_token else 'None'}")
    
    token = settings.BOT_TOKEN
    safe_token = f"{token[:5]}...{token[-5:]}" if token and len(token) > 10 else "INVALID_OR_EMPTY"
    logging.info(f" DEBUG: Initializing Bot with token: {safe_token} (Length: {len(token)})")
    
    bot = Bot(token=token)
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
