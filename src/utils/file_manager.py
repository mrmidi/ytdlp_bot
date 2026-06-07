import logging
import shutil
import uuid
from pathlib import Path

from src.config import TMP_DIR

logger = logging.getLogger(__name__)

def create_temp_dir() -> Path:
    """
    Create a unique temporary directory under the configured TMP_DIR.
    Returns:
        Path object pointing to the created directory.
    """
    unique_id = uuid.uuid4().hex
    job_dir = TMP_DIR / unique_id
    job_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created temporary job directory: {job_dir}")
    return job_dir

def cleanup_dir(path: Path) -> None:
    """
    Recursively delete a directory and all of its contents.
    
    Args:
        path: Path object pointing to the directory to delete.
    """
    if not path or not path.exists():
        return
        
    try:
        if path.is_dir():
            shutil.rmtree(path)
            logger.debug(f"Successfully deleted temporary directory: {path}")
        else:
            path.unlink(missing_ok=True)
            logger.debug(f"Successfully deleted file: {path}")
    except Exception as e:
        logger.error(f"Error during cleanup of path {path}: {e}", exc_info=True)
