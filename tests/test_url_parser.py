import pytest
from src.utils.url_parser import find_supported_url

@pytest.mark.parametrize(
    "text,expected_service,expected_url",
    [
        # YouTube watch links
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ("Check this: http://m.youtube.com/watch?v=dQw4w9WgXcQ!", "youtube", "http://m.youtube.com/watch?v=dQw4w9WgXcQ"),
        
        # YouTube Shorts links
        ("https://youtube.com/shorts/tPEE9ZwTmy0?feature=share", "youtube", "https://youtube.com/shorts/tPEE9ZwTmy0"),
        
        # YouTube share links (youtu.be)
        ("https://youtu.be/dQw4w9WgXcQ", "youtube", "https://youtu.be/dQw4w9WgXcQ"),
        
        # YouTube live links
        ("https://www.youtube.com/live/some-live-id", "youtube", "https://www.youtube.com/live/some-live-id"),
        
        # Twitter links
        ("https://twitter.com/NASA/status/1800000000000000000", "twitter", "https://twitter.com/NASA/status/1800000000000000000"),
        
        # X.com links
        ("http://x.com/jack/status/20", "twitter", "http://x.com/jack/status/20"),
        
        # Instagram posts and reels
        ("https://www.instagram.com/p/B-some_post_id/", "instagram", "https://www.instagram.com/p/B-some_post_id"),
        ("https://www.instagram.com/reel/C8C8a2hO3Lw/?igsh=MTZkdmN4N2g=", "instagram", "https://www.instagram.com/reel/C8C8a2hO3Lw"),
        ("https://instagram.com/tv/C8C8a2h/", "instagram", "https://instagram.com/tv/C8C8a2h"),
        
        # TikTok videos and mobile share links
        ("https://www.tiktok.com/@khaby.lame/video/1234567890123456789", "tiktok", "https://www.tiktok.com/@khaby.lame/video/1234567890123456789"),
        ("https://vm.tiktok.com/Zabcde/", "tiktok", "https://vm.tiktok.com/Zabcde/"),
        ("https://vt.tiktok.com/Zabcde/", "tiktok", "https://vt.tiktok.com/Zabcde/"),
    ]
)
def test_find_supported_url_success(text, expected_service, expected_url):
    result = find_supported_url(text)
    assert result is not None
    assert result[0] == expected_service
    assert result[1] == expected_url

@pytest.mark.parametrize(
    "text",
    [
        "hello world",
        "https://google.com",
        "https://youtube.com",  # Too short/incomplete
        "https://instagram.com/direct/inbox/",  # Non-video URL
        "http://x.com/jack",  # Non-status URL
    ]
)
def test_find_supported_url_none(text):
    assert find_supported_url(text) is None

def test_find_first_supported_url_in_multiple():
    text = "Here is a tweet https://x.com/a/status/123 and a video https://youtu.be/abc"
    result = find_supported_url(text)
    assert result is not None
    assert result[0] == "twitter"
    assert result[1] == "https://x.com/a/status/123"
