import shutil
import logging

logger = logging.getLogger(__name__)

def check_dependencies() -> bool:
    """
    Check if required system dependencies (like ffmpeg and ffprobe) are installed.
    Returns True if all dependencies are found, False otherwise.
    """
    required_binaries = ["ffmpeg", "ffprobe"]
    missing = []

    for binary in required_binaries:
        if shutil.which(binary) is None:
            missing.append(binary)

    if missing:
        logger.warning(
            f"⚠️ Missing required system dependencies: {', '.join(missing)}. "
            f"Some downloader features (like merging audio/video formats) might not work. "
            f"Please install them via brew/apt-get."
        )
        return False

    logger.info("✅ All system dependencies (ffmpeg, ffprobe) found in system PATH.")
    return True
