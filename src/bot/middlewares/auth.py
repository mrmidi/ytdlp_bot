import logging
from collections.abc import Callable, Awaitable
from typing import Any, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.config import SUPER_ADMIN_ID
from src.db.connection import async_session_maker
from src.db.repository import is_user_allowed

logger = logging.getLogger(__name__)

class AllowedUserMiddleware(BaseMiddleware):
    """Middleware to check if the sender is authorized to use the bot."""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Check if the event contains user information
        if not event.from_user:
            return
            
        user_id = event.from_user.id
        
        # Allow /request command to pass through to handlers for unauthorized users
        if event.text and event.text.strip().startswith("/request"):
            return await handler(event, data)
            
        # Super Admin is always allowed
        if user_id == SUPER_ADMIN_ID:
            return await handler(event, data)
            
        # Check database for allowed users
        async with async_session_maker() as session:
            allowed = await is_user_allowed(session, user_id)
            
        if allowed:
            return await handler(event, data)
            
        # User is not allowed - log and reply if it's a private chat
        logger.warning(f"Unauthorized access attempt by user ID {user_id} (@{event.from_user.username or 'No Username'})")
        
        if event.chat.type == "private":
            await event.answer(
                f"⚠️ You are not authorized to use this bot.\n"
                f"Please ask the administrator to allow your user ID: `{user_id}`"
            )
        # For non-private chats (groups/channels), we silently ignore the message.
        return
