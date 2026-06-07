import logging
from pathlib import Path
import yt_dlp

from src.services.base import BaseDownloader, DownloadResult

logger = logging.getLogger(__name__)

class YouTubeDownloader(BaseDownloader):
    """Downloader class for YouTube videos and Shorts using yt-dlp."""
    
    def download(self, url: str, output_dir: Path) -> DownloadResult:
        logger.info(f"Starting YouTube download for URL: {url}")
        
        # Output template using the video ID
        outtmpl = str(output_dir / "%(id)s.%(ext)s")
        
        ydl_opts = {
            # Prefer MP4 for inline Telegram video playback
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'outtmpl': outtmpl,
            'writethumbnail': True,
            'updatetime': False,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download and extract info
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            
            # Find the downloaded video file in the output directory
            downloaded_file = None
            # Check for standard extension options (prioritizing mp4)
            for ext in ['mp4', 'mkv', 'webm', '3gp']:
                f_path = output_dir / f"{video_id}.{ext}"
                if f_path.exists():
                    downloaded_file = f_path
                    break
                    
            if not downloaded_file:
                # Fallback: check if the exact prepare_filename exists
                filename = ydl.prepare_filename(info)
                path = Path(filename)
                if path.exists():
                    downloaded_file = path
                else:
                    # Scan output directory for any video files as last resort
                    for f in output_dir.iterdir():
                        if f.is_file() and f.suffix.lower() in ['.mp4', '.mkv', '.webm', '.mov', '.3gp']:
                            downloaded_file = f
                            break
                            
            if not downloaded_file:
                raise FileNotFoundError(f"Failed to find downloaded video file for ID {video_id} in {output_dir}")
                
            # Locate downloaded thumbnail
            thumbnail_file = None
            for ext in ['jpg', 'jpeg', 'png', 'webp']:
                t_path = output_dir / f"{video_id}.{ext}"
                if t_path.exists():
                    thumbnail_file = t_path
                    break
                    
            # Parse metadata
            title = info.get('title', 'YouTube Video')
            duration = info.get('duration')
            width = info.get('width')
            height = info.get('height')
            
            logger.info(f"Successfully downloaded YouTube video: {title} ({downloaded_file})")
            
            return DownloadResult(
                file_path=downloaded_file,
                title=title,
                thumbnail_path=thumbnail_file,
                duration=int(duration) if duration is not None else None,
                width=int(width) if width is not None else None,
                height=int(height) if height is not None else None
            )
