import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.services.downloader_factory import DownloaderFactory
from src.services.youtube import YouTubeDownloader
from src.services.twitter import TwitterDownloader
from src.services.instagram import InstagramDownloader
from src.services.tiktok import TikTokDownloader
from src.services.base import DownloadResult

def test_downloader_factory():
    # Test factory returns correct instances
    yt = DownloaderFactory.get_downloader("youtube")
    assert isinstance(yt, YouTubeDownloader)
    
    tw = DownloaderFactory.get_downloader("twitter")
    assert isinstance(tw, TwitterDownloader)
    
    ig = DownloaderFactory.get_downloader("instagram")
    assert isinstance(ig, InstagramDownloader)
    
    tk = DownloaderFactory.get_downloader("tiktok")
    assert isinstance(tk, TikTokDownloader)
    
    # Test unsupported service raises ValueError
    with pytest.raises(ValueError, match="Unsupported downloader service"):
        DownloaderFactory.get_downloader("unknown")

@pytest.mark.parametrize(
    "downloader_class,service_name",
    [
        (YouTubeDownloader, "youtube"),
        (TwitterDownloader, "twitter"),
        (InstagramDownloader, "instagram"),
        (TikTokDownloader, "tiktok"),
    ]
)
def test_downloader_implementations(downloader_class, service_name, tmp_path):
    # GIVEN: Mock info dictionary returned by yt-dlp
    mock_info = {
        'id': 'test_video_123',
        'title': f'Test {service_name.capitalize()} Video',
        'duration': 120,
        'width': 1920,
        'height': 1080,
    }
    
    # Create dummy files to simulate downloaded video and thumbnail
    video_file = tmp_path / "test_video_123.mp4"
    thumbnail_file = tmp_path / "test_video_123.jpg"
    video_file.write_text("dummy video content")
    thumbnail_file.write_text("dummy thumbnail content")
    
    downloader = downloader_class()
    
    # WHEN: Mocking the YoutubeDL context manager
    with patch("yt_dlp.YoutubeDL") as mock_ytdl_class:
        mock_ytdl_instance = MagicMock()
        mock_ytdl_class.return_value.__enter__.return_value = mock_ytdl_instance
        
        # Mock extract_info and prepare_filename
        mock_ytdl_instance.extract_info.return_value = mock_info
        mock_ytdl_instance.prepare_filename.return_value = str(video_file)
        
        result = downloader.download("https://dummyurl.com", tmp_path)
        
        # THEN: The downloader should call extract_info and return a populated DownloadResult
        mock_ytdl_instance.extract_info.assert_called_once_with("https://dummyurl.com", download=True)
        assert isinstance(result, DownloadResult)
        assert result.file_path == video_file
        assert result.title == mock_info['title']
        assert result.thumbnail_path == thumbnail_file
        assert result.duration == 120
        assert result.width == 1920
        assert result.height == 1080
