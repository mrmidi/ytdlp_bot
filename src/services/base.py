from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DownloadResult:
    """Dataclass holding details of a completed download."""
    file_path: Path
    title: str
    thumbnail_path: Path | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None

class BaseDownloader(ABC):
    """Abstract base class for service-specific downloaders."""
    
    @abstractmethod
    def download(self, url: str, output_dir: Path) -> DownloadResult:
        """
        Download a video from the given URL and save it to output_dir.
        
        Args:
            url: The video URL to download.
            output_dir: Directory where the file should be saved.
            
        Returns:
            A DownloadResult containing path and metadata.
            
        Raises:
            Exception if download fails.
        """
        pass
