import logging
from aiogram import Router, html
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from src.config import SUPER_ADMIN_ID
from src.db.connection import async_session_maker
from src.db.repository import is_user_allowed

logger = logging.getLogger(__name__)
router = Router(name="start")

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handler for the /start command."""
    welcome_text = (
        f"Hi {html.bold(message.from_user.full_name)}! 👋\n\n"
        f"I am a video downloader bot. Send me any supported video link (YouTube, Twitter/X, Instagram) "
        f"and I will download and send it back to you.\n\n"
        f"Use /help to see how to use me!"
    )
    await message.answer(welcome_text)

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handler for the /help command."""
    help_text = (
        f"🤖 {html.bold('How to use this bot:')}\n\n"
        f"1. Send me a URL to a video. Supported services:\n"
        f"   • YouTube / YouTube Shorts\n"
        f"   • Twitter / X\n"
        f"   • Instagram Reels / Posts\n\n"
        f"2. I will parse the URL, download the video, and send it as a Telegram Video message.\n"
        f"3. Temporary files are immediately cleaned up to save space.\n\n"
        f"🔐 {html.bold('Access Control:')}\n"
        f"Only allowed users can interact with this bot. If you are a Super Admin, you can use:\n"
        f"• <code>/allow &lt;user_id&gt; [username]</code> - Allow a user\n"
        f"• <code>/revoke &lt;user_id&gt;</code> - Revoke a user's access\n"
        f"• <code>/list</code> - List all allowed users"
    )
    await message.answer(help_text)

@router.message(Command("request"))
async def cmd_request(message: Message) -> None:
    """Request access to use the bot."""
    if not message.from_user:
        return
        
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # Check if user is already allowed (super admin or in DB)
    if user_id == SUPER_ADMIN_ID:
        await message.answer("You are the Super Admin. You already have access!")
        return
        
    async with async_session_maker() as session:
        allowed = await is_user_allowed(session, user_id)
        
    if allowed:
        await message.answer("You are already authorized to use this bot!")
        return
        
    # Send request notification to the super admin
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Allow ✅", callback_data=f"admin_allow:{user_id}"),
            InlineKeyboardButton(text="Deny ❌", callback_data=f"admin_deny:{user_id}")
        ]
    ])
    
    admin_msg = (
        f"🔔 {html.bold('Access Request:')}\n"
        f"User: {html.bold(full_name)}" + (f" (@{username})" if username else "") + f"\n"
        f"User ID: <code>{user_id}</code>"
    )
    
    try:
        await message.bot.send_message(
            chat_id=SUPER_ADMIN_ID,
            text=admin_msg,
            reply_markup=kb
        )
        await message.answer("📨 Your request for access has been sent to the administrator.")
    except Exception as e:
        logger.error(f"Failed to send access request to Super Admin {SUPER_ADMIN_ID}: {e}", exc_info=True)
        await message.answer("❌ Failed to send request to the administrator. Please try again later.")

