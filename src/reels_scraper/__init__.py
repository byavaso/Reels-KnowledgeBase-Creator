"""Instagram Reels Knowledge Base Creator."""

__version__ = "0.1.0"
__author__ = "Reels Scraper Team"
__description__ = "Extract, transcribe, and organize Instagram Reels into structured knowledge bases"

from .config import Config, get_config
from .logger import get_logger, setup_logger
from .models import (
    DownloadReport,
    DownloadStatus,
    MarkdownReport,
    ProfileMetadata,
    ReelMetadata,
    Transcript,
    TranscriptSegment,
)

__all__ = [
    "Config",
    "get_config",
    "get_logger",
    "setup_logger",
    "ProfileMetadata",
    "ReelMetadata",
    "DownloadStatus",
    "DownloadReport",
    "Transcript",
    "TranscriptSegment",
    "MarkdownReport",
]
