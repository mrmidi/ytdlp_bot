from src.services.base import BaseDownloader
from src.services.youtube import YouTubeDownloader
from src.services.twitter import TwitterDownloader
from src.services.instagram import InstagramDownloader
from src.services.tiktok import TikTokDownloader

class DownloaderFactory:
    """Factory to resolve and return appropriate downloader instances."""
    
    @staticmethod
    def get_downloader(service: str) -> BaseDownloader:
        """
        Get the downloader instance for the specified service name.
        
        Args:
            service: The name of the service (e.g. 'youtube', 'twitter', 'instagram', 'tiktok').
            
        Returns:
            An instance of BaseDownloader.
            
        Raises:
            ValueError: If the service is not supported.
        """
        service_lower = service.lower()
        if service_lower == "youtube":
            return YouTubeDownloader()
        elif service_lower == "twitter":
            return TwitterDownloader()
        elif service_lower == "instagram":
            return InstagramDownloader()
        elif service_lower == "tiktok":
            return TikTokDownloader()
        else:
            raise ValueError(f"Unsupported downloader service: {service}")
