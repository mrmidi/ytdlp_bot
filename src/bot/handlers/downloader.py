import asyncio
import logging
from pathlib import Path
from aiogram import Router, html
from aiogram.types import Message, FSInputFile
from aiogram.exceptions import TelegramAPIError

from src.utils.url_parser import find_supported_url
from src.utils.file_manager import create_temp_dir, cleanup_dir
from src.services.downloader_factory import DownloaderFactory
from src.config import TELEGRAM_API_SERVER_URL

logger = logging.getLogger(__name__)
router = Router(name="downloader")

# Determine file upload limits based on local Bot API server vs public server (2 GB vs 50 MB)
UPLOAD_LIMIT_BYTES = 2000 * 1024 * 1024 if TELEGRAM_API_SERVER_URL else 50 * 1024 * 1024
UPLOAD_LIMIT_MB = 2000 if TELEGRAM_API_SERVER_URL else 50

@router.message()
async def handle_url(message: Message) -> None:
    """Matches messages containing supported URLs and processes the download."""
    # Look for supported URLs in the message text
    url_data = find_supported_url(message.text)
    if not url_data:
        # Ignore messages that do not contain supported video URLs
        return
        
    service, url = url_data
    logger.info(f"Accepted URL download job: service={service}, url={url} from user={message.from_user.id}")
    
    # Send initial status message
    status_msg = await message.reply("⏳ Processing URL...")
    job_dir = create_temp_dir()
    
    try:
        # Resolve the downloader instance
        downloader = DownloaderFactory.get_downloader(service)
        
        # Update status
        await status_msg.edit_text("📥 Downloading video... Please wait.")
        
        # Download the video in a separate thread to avoid blocking the asyncio event loop
        result = await asyncio.to_thread(downloader.download, url, job_dir)
        
        # Verify if file exists
        if not result.file_path.exists():
            raise FileNotFoundError("Downloaded file was not found on disk.")
            
        # Check size of the file
        file_size = result.file_path.stat().st_size
        if file_size > UPLOAD_LIMIT_BYTES:
            size_mb = file_size / (1024 * 1024)
            await status_msg.edit_text(
                f"❌ The video is too large to send ({size_mb:.1f} MB).\n"
                f"Telegram Bot API limits uploads to {UPLOAD_LIMIT_MB} MB."
            )
            return
            
        # Update status
        await status_msg.edit_text("📤 Uploading video to Telegram...")
        
        # Prepare file wrappers
        video_file = FSInputFile(path=result.file_path)
        thumbnail_file = (
            FSInputFile(path=result.thumbnail_path)
            if result.thumbnail_path and result.thumbnail_path.exists()
            else None
        )
        
        # Upload the video without caption
        await message.reply_video(
            video=video_file,
            duration=result.duration,
            width=result.width,
            height=result.height,
            thumbnail=thumbnail_file,
            supports_streaming=True
        )
        
        # Send details in a separate message
        caption = f"🎥 {html.bold(result.title)}\n\nDownloaded via bot"
        await message.reply(caption)
        
        # Delete the status message on success
        await status_msg.delete()
        
    except TelegramAPIError as e:
        logger.error(f"Telegram API Error while uploading/replying: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Telegram upload error: {e.message}")
        
    except Exception as e:
        logger.error(f"Error processing download for {url}: {e}", exc_info=True)
        # Attempt to edit status message with friendly error
        try:
            await status_msg.edit_text(f"❌ Failed to download video: {str(e)[:100]}")
        except Exception:
            await message.reply(f"❌ Failed to download video: {str(e)[:100]}")
            
    finally:
        # Guarantee that all temporary files for this job are deleted
        cleanup_dir(job_dir)
