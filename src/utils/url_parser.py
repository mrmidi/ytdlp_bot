import re

# Regex patterns for identifying supported video services
YOUTUBE_PATTERN = re.compile(
    r'https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|v/|embed/|shorts/|live/)|youtu\.be/)[a-zA-Z0-9_-]+',
    re.IGNORECASE
)

TWITTER_PATTERN = re.compile(
    r'https?://(?:www\.)?(?:twitter|x)\.com/[a-zA-Z0-9_]+/status/\d+',
    re.IGNORECASE
)

INSTAGRAM_PATTERN = re.compile(
    r'https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[a-zA-Z0-9_-]+',
    re.IGNORECASE
)

TIKTOK_PATTERN = re.compile(
    r'https?://(?:www\.|vm\.|vt\.)?tiktok\.com/(?:@[\w.-]+/video/\d+|[a-zA-Z0-9_-]+)/?',
    re.IGNORECASE
)

def find_supported_url(text: str) -> tuple[str, str] | None:
    """
    Search the text for a supported URL.
    Returns a tuple of (service_name, matched_url) or None if no supported URL is found.
    """
    if not text:
        return None

    matches = []

    # Check YouTube pattern
    youtube_match = YOUTUBE_PATTERN.search(text)
    if youtube_match:
        matches.append((youtube_match.start(), "youtube", youtube_match.group(0)))

    # Check Twitter / X pattern
    twitter_match = TWITTER_PATTERN.search(text)
    if twitter_match:
        matches.append((twitter_match.start(), "twitter", twitter_match.group(0)))

    # Check Instagram pattern
    instagram_match = INSTAGRAM_PATTERN.search(text)
    if instagram_match:
        matches.append((instagram_match.start(), "instagram", instagram_match.group(0)))

    # Check TikTok pattern
    tiktok_match = TIKTOK_PATTERN.search(text)
    if tiktok_match:
        matches.append((tiktok_match.start(), "tiktok", tiktok_match.group(0)))

    if not matches:
        return None

    # Sort matches by their starting index in the text and return the first one
    matches.sort(key=lambda x: x[0])
    return matches[0][1], matches[0][2]
