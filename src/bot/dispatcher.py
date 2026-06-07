from aiogram import Dispatcher
from src.bot.middlewares.auth import AllowedUserMiddleware
from src.bot.handlers.start import router as start_router
from src.bot.handlers.admin import router as admin_router
from src.bot.handlers.downloader import router as downloader_router

def get_dispatcher() -> Dispatcher:
    """Initialize the dispatcher and register routers and middlewares."""
    dp = Dispatcher()
    
    # Register outer middleware to check user permissions before running handlers and filters
    dp.message.outer_middleware(AllowedUserMiddleware())
    
    # Register handlers
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(downloader_router)
    
    return dp
