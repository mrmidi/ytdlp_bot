import asyncio
import logging
import sys
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import BOT_TOKEN, SUPER_ADMIN_ID
from src.db.connection import init_db, seed_super_admin
from src.bot.dispatcher import get_dispatcher
from src.services.dependency_check import check_dependencies

# Configure logging to standard output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

async def main() -> None:
    # 1. Verify system dependencies (like FFMpeg)
    check_dependencies()
    
    # 2. Check for bot token
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN is not set in the environment or .env file. Exiting.")
        sys.exit(1)
        
    # 3. Initialize database tables and seed Super Admin
    try:
        await init_db()
        await seed_super_admin(SUPER_ADMIN_ID)
    except Exception as e:
        logger.critical(f"❌ Database initialization failed: {e}", exc_info=True)
        sys.exit(1)
        
    # 4. Initialize bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = get_dispatcher()
    
    logger.info("🤖 Starting Telegram Bot polling...")
    
    # 5. Start long polling
    try:
        # Delete webhook before polling to clear any leftover hook on Telegram's side
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"🤖 Bot polling stopped due to an error: {e}", exc_info=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
