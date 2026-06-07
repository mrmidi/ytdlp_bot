import logging
from pathlib import Path
import yt_dlp

from src.services.base import BaseDownloader, DownloadResult

logger = logging.getLogger(__name__)

class TikTokDownloader(BaseDownloader):
    """Downloader class for TikTok videos using yt-dlp."""
    
    def download(self, url: str, output_dir: Path) -> DownloadResult:
        logger.info(f"Starting TikTok download for URL: {url}")
        
        outtmpl = str(output_dir / "%(id)s.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'outtmpl': outtmpl,
            'writethumbnail': True,
            'updatetime': False,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            # TikTok has aggressive scraper protection, use browser-like headers
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            
            # Find the downloaded video file in the output directory
            downloaded_file = None
            for ext in ['mp4', 'mkv', 'webm']:
                f_path = output_dir / f"{video_id}.{ext}"
                if f_path.exists():
                    downloaded_file = f_path
                    break
                    
            if not downloaded_file:
                filename = ydl.prepare_filename(info)
                path = Path(filename)
                if path.exists():
                    downloaded_file = path
                else:
                    for f in output_dir.iterdir():
                        if f.is_file() and f.suffix.lower() in ['.mp4', '.mkv', '.webm', '.mov']:
                            downloaded_file = f
                            break
                            
            if not downloaded_file:
                raise FileNotFoundError(f"Failed to find downloaded TikTok video file for ID {video_id} in {output_dir}")
                
            # Locate downloaded thumbnail
            thumbnail_file = None
            for ext in ['jpg', 'jpeg', 'png', 'webp']:
                t_path = output_dir / f"{video_id}.{ext}"
                if t_path.exists():
                    thumbnail_file = t_path
                    break
                    
            # Parse metadata
            title = info.get('title', 'TikTok Video')
            duration = info.get('duration')
            width = info.get('width')
            height = info.get('height')
            
            logger.info(f"Successfully downloaded TikTok video: {title} ({downloaded_file})")
            
            return DownloadResult(
                file_path=downloaded_file,
                title=title,
                thumbnail_path=thumbnail_file,
                duration=int(duration) if duration is not None else None,
                width=int(width) if width is not None else None,
                height=int(height) if height is not None else None
            )
