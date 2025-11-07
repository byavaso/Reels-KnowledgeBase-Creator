"""Data models for Instagram Reels Knowledge Base Creator."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


# ==================== Instagram Models ====================


class ProfileMetadata(BaseModel):
    """Instagram profile metadata."""

    username: str = Field(..., description="Instagram username")
    full_name: str = Field(default="", description="Full display name")
    biography: str = Field(default="", description="Profile biography")
    profile_pic_url: Optional[str] = Field(default=None, description="Profile picture URL")
    follower_count: int = Field(default=0, ge=0, description="Number of followers")
    following_count: int = Field(default=0, ge=0, description="Number of following")
    post_count: int = Field(default=0, ge=0, description="Number of posts")
    is_verified: bool = Field(default=False, description="Verification status")
    is_business: bool = Field(default=False, description="Business account status")
    scraped_at: datetime = Field(default_factory=datetime.now, description="Scraping timestamp")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ReelMetadata(BaseModel):
    """Instagram Reel metadata."""

    video_id: str = Field(..., description="Unique video identifier")
    shortcode: str = Field(..., description="Instagram shortcode")
    url: str = Field(..., description="Video URL")
    caption: str = Field(default="", description="Video caption")
    timestamp: datetime = Field(..., description="Publication timestamp")
    view_count: int = Field(default=0, ge=0, description="Number of views")
    like_count: int = Field(default=0, ge=0, description="Number of likes")
    comment_count: int = Field(default=0, ge=0, description="Number of comments")
    video_url: str = Field(..., description="Direct video download URL")
    duration: float = Field(default=0.0, ge=0, description="Video duration in seconds")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail URL")
    owner_username: str = Field(default="", description="Video owner username")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ==================== Download Models ====================


class DownloadStatus(BaseModel):
    """Status of a video download."""

    video_id: str = Field(..., description="Video identifier")
    success: bool = Field(..., description="Download success status")
    file_path: Optional[Path] = Field(default=None, description="Downloaded file path")
    file_size: int = Field(default=0, ge=0, description="File size in bytes")
    download_time: float = Field(default=0.0, ge=0, description="Download time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    retry_count: int = Field(default=0, ge=0, description="Number of retries")
    timestamp: datetime = Field(default_factory=datetime.now, description="Download timestamp")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat(), Path: lambda v: str(v)}


class DownloadReport(BaseModel):
    """Report of batch download operation."""

    total_videos: int = Field(default=0, ge=0, description="Total videos to download")
    successful: int = Field(default=0, ge=0, description="Successfully downloaded")
    failed: int = Field(default=0, ge=0, description="Failed downloads")
    skipped: int = Field(default=0, ge=0, description="Skipped (already exists)")
    total_size: int = Field(default=0, ge=0, description="Total size in bytes")
    total_time: float = Field(default=0.0, ge=0, description="Total time in seconds")
    download_statuses: List[DownloadStatus] = Field(
        default_factory=list, description="Individual download statuses"
    )
    started_at: datetime = Field(default_factory=datetime.now, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ==================== Transcription Models ====================


class TranscriptSegment(BaseModel):
    """Individual segment of a transcript with timestamp."""

    start_time: float = Field(..., ge=0, description="Segment start time in seconds")
    end_time: float = Field(..., ge=0, description="Segment end time in seconds")
    text: str = Field(..., description="Transcript text for this segment")
    speaker: Optional[str] = Field(default=None, description="Speaker identifier if detected")

    def formatted_time(self, seconds: float) -> str:
        """Format seconds as MM:SS.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    @property
    def formatted_start(self) -> str:
        """Get formatted start time."""
        return self.formatted_time(self.start_time)

    @property
    def formatted_end(self) -> str:
        """Get formatted end time."""
        return self.formatted_time(self.end_time)


class Transcript(BaseModel):
    """Complete transcript of a video."""

    video_id: str = Field(..., description="Video identifier")
    text: str = Field(..., description="Full transcript text")
    language: str = Field(..., description="Detected or specified language code")
    segments: List[TranscriptSegment] = Field(
        default_factory=list, description="Timestamped segments"
    )
    confidence: float = Field(default=0.0, ge=0, le=1, description="Overall confidence score")
    duration: float = Field(default=0.0, ge=0, description="Total duration in seconds")
    word_count: int = Field(default=0, ge=0, description="Number of words")
    service: str = Field(default="", description="Transcription service used")
    model: str = Field(default="", description="Model used for transcription")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def get_formatted_transcript(self) -> str:
        """Get transcript formatted with timestamps.

        Returns:
            Formatted transcript string
        """
        if not self.segments:
            return self.text

        lines = []
        for segment in self.segments:
            lines.append(f"[{segment.formatted_start}] {segment.text}")
        return "\n".join(lines)


# ==================== Content Processing Models ====================


class MarkdownReport(BaseModel):
    """Markdown report generated from transcript."""

    video_id: str = Field(..., description="Video identifier")
    title: str = Field(..., description="Report title")
    content: str = Field(..., description="Full markdown content")
    summary: str = Field(default="", description="Executive summary")
    topics: List[str] = Field(default_factory=list, description="Extracted topics/tags")
    key_points: List[str] = Field(default_factory=list, description="Key takeaways")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    file_path: Optional[Path] = Field(default=None, description="Path to markdown file")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat(), Path: lambda v: str(v)}


# ==================== Pipeline Models ====================


@dataclass
class ErrorLog:
    """Error log entry."""

    timestamp: datetime
    stage: str
    video_id: Optional[str]
    error_type: str
    error_message: str
    traceback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "stage": self.stage,
            "video_id": self.video_id,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "traceback": self.traceback,
        }


@dataclass
class PipelineState:
    """State of the processing pipeline."""

    profile: Optional[ProfileMetadata] = None
    reels_discovered: int = 0
    reels_downloaded: int = 0
    reels_transcribed: int = 0
    reels_processed: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    errors: List[ErrorLog] = field(default_factory=list)
    current_stage: str = "idle"
    output_dir: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "profile": self.profile.model_dump() if self.profile else None,
            "reels_discovered": self.reels_discovered,
            "reels_downloaded": self.reels_downloaded,
            "reels_transcribed": self.reels_transcribed,
            "reels_processed": self.reels_processed,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "errors": [e.to_dict() for e in self.errors],
            "current_stage": self.current_stage,
            "output_dir": str(self.output_dir) if self.output_dir else None,
        }

    @property
    def has_errors(self) -> bool:
        """Check if pipeline has any errors."""
        return len(self.errors) > 0

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.reels_discovered == 0:
            return 0.0
        return (self.reels_processed / self.reels_discovered) * 100


# ==================== Statistics Models ====================


@dataclass
class Statistics:
    """Knowledge base statistics."""

    total_videos: int = 0
    total_duration: float = 0.0  # in seconds
    topic_distribution: Dict[str, int] = field(default_factory=dict)
    language_distribution: Dict[str, int] = field(default_factory=dict)
    date_range: Optional[tuple[datetime, datetime]] = None
    average_video_length: float = 0.0
    total_word_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_videos": self.total_videos,
            "total_duration": self.total_duration,
            "total_duration_formatted": self._format_duration(self.total_duration),
            "topic_distribution": self.topic_distribution,
            "language_distribution": self.language_distribution,
            "date_range": {
                "start": self.date_range[0].isoformat() if self.date_range else None,
                "end": self.date_range[1].isoformat() if self.date_range else None,
            }
            if self.date_range
            else None,
            "average_video_length": self.average_video_length,
            "average_video_length_formatted": self._format_duration(self.average_video_length),
            "total_word_count": self.total_word_count,
        }

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
