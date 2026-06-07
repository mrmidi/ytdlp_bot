import logging
import re
from aiogram import Router, html
from aiogram.filters import Command, BaseFilter
from aiogram.types import Message, CallbackQuery, TelegramObject

from src.config import SUPER_ADMIN_ID
from src.db.connection import async_session_maker
from src.db.repository import add_user, remove_user, list_users

logger = logging.getLogger(__name__)
router = Router(name="admin")

class IsSuperAdmin(BaseFilter):
    """Filter to check if the sender is the Super Admin."""
    async def __call__(self, event: TelegramObject) -> bool:
        return event.from_user is not None and event.from_user.id == SUPER_ADMIN_ID

# Apply filter to all handlers in this router
router.message.filter(IsSuperAdmin())
router.callback_query.filter(IsSuperAdmin())

@router.message(Command("allow"))
async def cmd_allow(message: Message) -> None:
    """Allow a user to use the bot. Format: /allow <user_id> [username]"""
    args = message.text.split()[1:]
    if not args:
        await message.answer("❌ Usage: <code>/allow &lt;user_id&gt; [username]</code>")
        return
        
    try:
        target_user_id = int(args[0])
    except ValueError:
        await message.answer("❌ Invalid user ID. Must be an integer.")
        return
        
    username = args[1] if len(args) > 1 else None
    
    async with async_session_maker() as session:
        async with session.begin():
            await add_user(session, target_user_id, username)
            
    username_str = f" (@{username})" if username else ""
    await message.answer(f"✅ User `{target_user_id}`{username_str} has been allowed.")
    logger.info(f"Admin allowed user {target_user_id}{username_str}")

@router.message(Command("revoke"))
async def cmd_revoke(message: Message) -> None:
    """Revoke a user's access. Format: /revoke <user_id>"""
    args = message.text.split()[1:]
    if not args:
        await message.answer("❌ Usage: <code>/revoke &lt;user_id&gt;</code>")
        return
        
    try:
        target_user_id = int(args[0])
    except ValueError:
        await message.answer("❌ Invalid user ID. Must be an integer.")
        return
        
    if target_user_id == SUPER_ADMIN_ID:
        await message.answer("❌ Cannot revoke access from the Super Admin.")
        return
        
    async with async_session_maker() as session:
        async with session.begin():
            removed = await remove_user(session, target_user_id)
            
    if removed:
        await message.answer(f"✅ Access revoked for user `{target_user_id}`.")
        logger.info(f"Admin revoked user {target_user_id}")
    else:
        await message.answer(f"❌ User `{target_user_id}` was not found in the allowed list.")

@router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    """List all allowed users."""
    async with async_session_maker() as session:
        users = await list_users(session)
        
    if not users:
        await message.answer("No allowed users found (except Super Admin).")
        return
        
    response = [f"📋 {html.bold('Allowed Users:')}\n"]
    for idx, u in enumerate(users, start=1):
        username_val = f" (@{u.username})" if u.username else ""
        date_str = u.added_at.strftime("%Y-%m-%d %H:%M")
        response.append(f"{idx}. `{u.user_id}`{username_val} — added {date_str}")
        
    await message.answer("\n".join(response))

@router.callback_query(lambda c: c.data and c.data.startswith("admin_allow:"))
async def handle_callback_allow(callback_query: CallbackQuery) -> None:
    """Callback handler for the Super Admin to allow a user."""
    data = callback_query.data.split(":")
    target_user_id = int(data[1])
    
    # Extract username from the original request message
    username = None
    if callback_query.message and callback_query.message.text:
        username_match = re.search(r'@(\w+)', callback_query.message.text)
        if username_match:
            username = username_match.group(1)
            
    async with async_session_maker() as session:
        async with session.begin():
            await add_user(session, target_user_id, username)
            
    # Notify the requester
    try:
        await callback_query.bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 {html.bold('Access Granted!')} You can now use the bot. Send me any supported video link!"
        )
    except Exception as e:
        logger.warning(f"Could not notify user {target_user_id} of access approval: {e}")
        
    # Edit the admin's original notification message
    username_str = f" (@{username})" if username else ""
    await callback_query.message.edit_text(
        f"✅ {html.bold('Allowed user:')} <code>{target_user_id}</code>{username_str}."
    )
    await callback_query.answer("User allowed.")

@router.callback_query(lambda c: c.data and c.data.startswith("admin_deny:"))
async def handle_callback_deny(callback_query: CallbackQuery) -> None:
    """Callback handler for the Super Admin to deny a user."""
    data = callback_query.data.split(":")
    target_user_id = int(data[1])
    
    username = None
    if callback_query.message and callback_query.message.text:
        username_match = re.search(r'@(\w+)', callback_query.message.text)
        if username_match:
            username = username_match.group(1)
            
    # Notify the requester
    try:
        await callback_query.bot.send_message(
            chat_id=target_user_id,
            text="❌ Your access request was denied by the administrator."
        )
    except Exception as e:
        logger.warning(f"Could not notify user {target_user_id} of access denial: {e}")
        
    # Edit the admin's original notification message
    username_str = f" (@{username})" if username else ""
    await callback_query.message.edit_text(
        f"❌ {html.bold('Denied user:')} <code>{target_user_id}</code>{username_str}."
    )
    await callback_query.answer("User denied.")

