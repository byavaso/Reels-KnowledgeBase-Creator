"""Video downloader for Instagram Reels."""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yt_dlp
from tqdm import tqdm

from ..logger import get_logger
from ..models import DownloadReport, DownloadStatus, ReelMetadata

logger = get_logger(__name__)


class VideoDownloader:
    """Download Instagram Reels videos concurrently."""

    def __init__(
        self,
        max_workers: int = 3,
        retry_count: int = 3,
        retry_delay: float = 5.0,
        output_dir: Path = Path("./output/downloads"),
        skip_existing: bool = True,
    ):
        """Initialize video downloader.

        Args:
            max_workers: Number of concurrent download workers
            retry_count: Number of retry attempts for failed downloads
            retry_delay: Initial delay for retry in seconds (exponential backoff)
            output_dir: Directory to save downloaded videos
            skip_existing: Skip already downloaded videos
        """
        self.max_workers = max_workers
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.output_dir = output_dir
        self.skip_existing = skip_existing

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Video downloader initialized: {max_workers} workers, "
            f"output: {output_dir}, retry: {retry_count}"
        )

    def _get_video_path(self, reel: ReelMetadata) -> Path:
        """Get output path for video file.

        Args:
            reel: Reel metadata

        Returns:
            Path to video file
        """
        filename = f"{reel.video_id}_{reel.shortcode}.mp4"
        return self.output_dir / filename

    def _is_video_downloaded(self, reel: ReelMetadata) -> bool:
        """Check if video is already downloaded.

        Args:
            reel: Reel metadata

        Returns:
            True if video exists and is valid
        """
        video_path = self._get_video_path(reel)

        if not video_path.exists():
            return False

        # Check if file size is reasonable (> 1KB)
        if video_path.stat().st_size < 1024:
            logger.warning(f"Found incomplete download: {video_path}")
            return False

        return True

    def download_single(
        self, reel: ReelMetadata, progress_bar: Optional[tqdm] = None
    ) -> DownloadStatus:
        """Download a single video with retry logic.

        Args:
            reel: Reel metadata
            progress_bar: Optional progress bar to update

        Returns:
            DownloadStatus instance
        """
        video_path = self._get_video_path(reel)
        start_time = time.time()

        # Check if already downloaded
        if self.skip_existing and self._is_video_downloaded(reel):
            logger.debug(f"Skipping already downloaded video: {reel.shortcode}")
            if progress_bar:
                progress_bar.set_postfix_str(f"Skipped: {reel.shortcode}")
            return DownloadStatus(
                video_id=reel.video_id,
                success=True,
                file_path=video_path,
                file_size=video_path.stat().st_size,
                download_time=0.0,
                error_message="Already downloaded (skipped)",
                retry_count=0,
            )

        # Try downloading with retries
        for attempt in range(self.retry_count + 1):
            try:
                if progress_bar:
                    progress_bar.set_postfix_str(
                        f"Downloading: {reel.shortcode} (attempt {attempt + 1})"
                    )

                # Configure yt-dlp options
                ydl_opts = {
                    "format": "best",
                    "outtmpl": str(video_path),
                    "quiet": True,
                    "no_warnings": True,
                    "extract_flat": False,
                    # Instagram-specific options
                    "http_headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                }

                # Download video
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([reel.url])

                # Verify download
                if not video_path.exists():
                    raise FileNotFoundError(f"Downloaded file not found: {video_path}")

                file_size = video_path.stat().st_size
                download_time = time.time() - start_time

                logger.info(
                    f"Downloaded {reel.shortcode}: {file_size / 1024 / 1024:.2f} MB "
                    f"in {download_time:.1f}s"
                )

                if progress_bar:
                    progress_bar.set_postfix_str(f"✓ {reel.shortcode}")
                    progress_bar.update(1)

                return DownloadStatus(
                    video_id=reel.video_id,
                    success=True,
                    file_path=video_path,
                    file_size=file_size,
                    download_time=download_time,
                    error_message=None,
                    retry_count=attempt,
                )

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"Download attempt {attempt + 1}/{self.retry_count + 1} failed "
                    f"for {reel.shortcode}: {error_msg}"
                )

                # If not the last attempt, wait before retry (exponential backoff)
                if attempt < self.retry_count:
                    wait_time = self.retry_delay * (2**attempt)
                    logger.debug(f"Waiting {wait_time:.1f}s before retry")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    logger.error(f"Download failed for {reel.shortcode} after all retries")
                    if progress_bar:
                        progress_bar.set_postfix_str(f"✗ {reel.shortcode}")
                        progress_bar.update(1)

                    return DownloadStatus(
                        video_id=reel.video_id,
                        success=False,
                        file_path=None,
                        file_size=0,
                        download_time=time.time() - start_time,
                        error_message=error_msg,
                        retry_count=attempt,
                    )

        # Should not reach here
        return DownloadStatus(
            video_id=reel.video_id,
            success=False,
            file_path=None,
            file_size=0,
            download_time=time.time() - start_time,
            error_message="Unknown error",
            retry_count=self.retry_count,
        )

    def download_batch(
        self, reels: List[ReelMetadata], show_progress: bool = True
    ) -> DownloadReport:
        """Download multiple videos concurrently.

        Args:
            reels: List of Reel metadata
            show_progress: Show progress bar

        Returns:
            DownloadReport with statistics
        """
        logger.info(f"Starting batch download of {len(reels)} videos")
        report = DownloadReport(
            total_videos=len(reels), started_at=datetime.now(), download_statuses=[]
        )

        # Create progress bar
        progress_bar = None
        if show_progress:
            progress_bar = tqdm(
                total=len(reels),
                desc="Downloading videos",
                unit="video",
                dynamic_ncols=True,
            )

        try:
            # Download videos concurrently
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all download tasks
                future_to_reel = {
                    executor.submit(self.download_single, reel, progress_bar): reel
                    for reel in reels
                }

                # Process completed downloads
                for future in as_completed(future_to_reel):
                    reel = future_to_reel[future]
                    try:
                        status = future.result()
                        report.download_statuses.append(status)

                        # Update statistics
                        if status.success:
                            if status.error_message == "Already downloaded (skipped)":
                                report.skipped += 1
                            else:
                                report.successful += 1
                                report.total_size += status.file_size
                        else:
                            report.failed += 1

                    except Exception as e:
                        logger.error(f"Error processing download result for {reel.shortcode}: {e}")
                        report.failed += 1

        finally:
            if progress_bar:
                progress_bar.close()

        # Finalize report
        report.completed_at = datetime.now()
        report.total_time = (report.completed_at - report.started_at).total_seconds()

        logger.info(
            f"Batch download complete: {report.successful} successful, "
            f"{report.failed} failed, {report.skipped} skipped in {report.total_time:.1f}s"
        )

        return report

    def save_download_report(self, report: DownloadReport, output_path: Path) -> None:
        """Save download report to JSON file.

        Args:
            report: Download report to save
            output_path: Path to save report
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(), f, indent=2, default=str)

            logger.info(f"Download report saved to {output_path}")

        except Exception as e:
            logger.error(f"Failed to save download report: {e}")


def load_reels_from_json(json_path: Path) -> List[ReelMetadata]:
    """Load Reels metadata from JSON file.

    Args:
        json_path: Path to reels_list.json file

    Returns:
        List of ReelMetadata instances
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        reels = [ReelMetadata(**reel_data) for reel_data in data]
        logger.info(f"Loaded {len(reels)} Reels from {json_path}")
        return reels

    except Exception as e:
        logger.error(f"Failed to load Reels from {json_path}: {e}")
        raise
