"""Progress tracking and resume capability."""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from .logger import get_logger

logger = get_logger(__name__)


class ProgressStatus(str, Enum):
    """Status of a progress item."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProgressItem(BaseModel):
    """Single item in progress tracking."""

    item_id: str = Field(..., description="Unique identifier for the item")
    status: ProgressStatus = Field(default=ProgressStatus.PENDING, description="Current status")
    started_at: Optional[datetime] = Field(default=None, description="When processing started")
    completed_at: Optional[datetime] = Field(default=None, description="When processing completed")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ProgressTracker(BaseModel):
    """Track progress of batch operations with resume capability."""

    stage: str = Field(..., description="Name of the stage (e.g., 'download', 'transcribe')")
    total_items: int = Field(default=0, description="Total number of items to process")
    items: Dict[str, ProgressItem] = Field(default_factory=dict, description="Progress items")
    started_at: Optional[datetime] = Field(default=None, description="When stage started")
    completed_at: Optional[datetime] = Field(default=None, description="When stage completed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Stage metadata")

    @property
    def pending_items(self) -> List[str]:
        """Get list of pending item IDs."""
        return [
            item_id
            for item_id, item in self.items.items()
            if item.status == ProgressStatus.PENDING
        ]

    @property
    def completed_items(self) -> List[str]:
        """Get list of completed item IDs."""
        return [
            item_id
            for item_id, item in self.items.items()
            if item.status == ProgressStatus.COMPLETED
        ]

    @property
    def failed_items(self) -> List[str]:
        """Get list of failed item IDs."""
        return [
            item_id
            for item_id, item in self.items.items()
            if item.status == ProgressStatus.FAILED
        ]

    @property
    def in_progress_items(self) -> List[str]:
        """Get list of in-progress item IDs."""
        return [
            item_id
            for item_id, item in self.items.items()
            if item.status == ProgressStatus.IN_PROGRESS
        ]

    @property
    def completion_rate(self) -> float:
        """Get completion rate as percentage."""
        if self.total_items == 0:
            return 0.0
        return (len(self.completed_items) / self.total_items) * 100

    @property
    def is_complete(self) -> bool:
        """Check if all items are completed or failed."""
        return len(self.pending_items) == 0 and len(self.in_progress_items) == 0

    def add_item(self, item_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a new item to track.

        Args:
            item_id: Unique identifier for the item
            metadata: Optional metadata for the item
        """
        if item_id not in self.items:
            self.items[item_id] = ProgressItem(
                item_id=item_id,
                metadata=metadata or {},
            )
            self.total_items = len(self.items)
            logger.debug(f"Added item to progress: {item_id}")

    def start_item(self, item_id: str) -> None:
        """Mark an item as in progress.

        Args:
            item_id: Item identifier
        """
        if item_id in self.items:
            self.items[item_id].status = ProgressStatus.IN_PROGRESS
            self.items[item_id].started_at = datetime.now()
            logger.debug(f"Started item: {item_id}")

    def complete_item(
        self, item_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark an item as completed.

        Args:
            item_id: Item identifier
            metadata: Optional metadata to merge
        """
        if item_id in self.items:
            self.items[item_id].status = ProgressStatus.COMPLETED
            self.items[item_id].completed_at = datetime.now()
            if metadata:
                self.items[item_id].metadata.update(metadata)
            logger.debug(f"Completed item: {item_id}")

    def fail_item(self, item_id: str, error: str) -> None:
        """Mark an item as failed.

        Args:
            item_id: Item identifier
            error: Error message
        """
        if item_id in self.items:
            self.items[item_id].status = ProgressStatus.FAILED
            self.items[item_id].completed_at = datetime.now()
            self.items[item_id].error = error
            logger.debug(f"Failed item: {item_id} - {error}")

    def skip_item(self, item_id: str, reason: Optional[str] = None) -> None:
        """Mark an item as skipped.

        Args:
            item_id: Item identifier
            reason: Optional reason for skipping
        """
        if item_id in self.items:
            self.items[item_id].status = ProgressStatus.SKIPPED
            self.items[item_id].completed_at = datetime.now()
            if reason:
                self.items[item_id].metadata["skip_reason"] = reason
            logger.debug(f"Skipped item: {item_id}")

    def get_resumable_items(self) -> List[str]:
        """Get list of items that can be resumed (pending + failed in-progress).

        Returns:
            List of item IDs that should be processed
        """
        resumable = []

        # Add pending items
        resumable.extend(self.pending_items)

        # Add in-progress items (crashed without completing)
        resumable.extend(self.in_progress_items)

        return resumable

    def start(self) -> None:
        """Mark the stage as started."""
        if not self.started_at:
            self.started_at = datetime.now()
            logger.info(f"Started stage: {self.stage}")

    def complete(self) -> None:
        """Mark the stage as completed."""
        if not self.completed_at:
            self.completed_at = datetime.now()
            logger.info(f"Completed stage: {self.stage}")

    def save(self, file_path: Path) -> None:
        """Save progress to JSON file.

        Args:
            file_path: Path to save progress file
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.model_dump(), f, indent=2, default=str)

            logger.debug(f"Saved progress to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    @classmethod
    def load(cls, file_path: Path) -> Optional["ProgressTracker"]:
        """Load progress from JSON file.

        Args:
            file_path: Path to progress file

        Returns:
            ProgressTracker instance or None if file doesn't exist
        """
        try:
            if not file_path.exists():
                logger.debug(f"Progress file not found: {file_path}")
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracker = cls(**data)
            logger.info(
                f"Loaded progress for stage '{tracker.stage}': "
                f"{len(tracker.completed_items)}/{tracker.total_items} completed"
            )

            return tracker

        except Exception as e:
            logger.error(f"Failed to load progress: {e}")
            return None

    @classmethod
    def create_or_load(
        cls, stage: str, file_path: Path, item_ids: Optional[List[str]] = None
    ) -> "ProgressTracker":
        """Create new tracker or load existing one.

        Args:
            stage: Stage name
            file_path: Path to progress file
            item_ids: Optional list of item IDs to initialize with

        Returns:
            ProgressTracker instance
        """
        # Try to load existing progress
        tracker = cls.load(file_path)

        if tracker:
            # Reset in-progress items to pending (in case of crash)
            for item_id in tracker.in_progress_items:
                tracker.items[item_id].status = ProgressStatus.PENDING
                logger.debug(f"Reset in-progress item to pending: {item_id}")

            return tracker

        # Create new tracker
        tracker = cls(stage=stage)

        if item_ids:
            for item_id in item_ids:
                tracker.add_item(item_id)

        tracker.start()
        tracker.save(file_path)

        return tracker

    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary.

        Returns:
            Dictionary with summary statistics
        """
        return {
            "stage": self.stage,
            "total_items": self.total_items,
            "completed": len(self.completed_items),
            "failed": len(self.failed_items),
            "pending": len(self.pending_items),
            "in_progress": len(self.in_progress_items),
            "completion_rate": f"{self.completion_rate:.1f}%",
            "is_complete": self.is_complete,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
