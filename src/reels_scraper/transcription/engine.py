"""Transcription engine for processing videos."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from tqdm import tqdm

from ..logger import get_logger
from ..models import Transcript
from ..progress import ProgressTracker
from .audio_extractor import AudioExtractor
from .whisper_service import WhisperService

logger = get_logger(__name__)


class TranscriptionEngine:
    """Engine for transcribing videos using Whisper API."""

    def __init__(
        self,
        api_key: str,
        model: str = "whisper-1",
        language: str = "auto",
        max_workers: int = 2,
        include_timestamps: bool = True,
        enable_resume: bool = True,
        progress_file: Optional[Path] = None,
        output_dir: Path = Path("./output/transcripts"),
    ):
        """Initialize transcription engine.

        Args:
            api_key: OpenAI API key
            model: Whisper model to use
            language: Language code or 'auto' for detection
            max_workers: Number of concurrent transcription workers
            include_timestamps: Include timestamps in transcripts
            enable_resume: Enable resume capability with progress tracking
            progress_file: Custom path for progress file
            output_dir: Output directory (for default progress file path)
        """
        self.audio_extractor = AudioExtractor()
        self.whisper_service = WhisperService(
            api_key=api_key,
            model=model,
            language=language if language != "auto" else None,
        )
        self.max_workers = max_workers
        self.include_timestamps = include_timestamps
        self.enable_resume = enable_resume
        self.progress_file = progress_file or (output_dir / ".transcription_progress.json")

        # Check ffmpeg availability
        if not AudioExtractor.check_ffmpeg_installed():
            logger.warning("ffmpeg not found - audio extraction may fail")

        logger.info(
            f"Transcription engine initialized: {model}, "
            f"language={language}, workers={max_workers}, resume={enable_resume}"
        )

    def transcribe_video(
        self, video_path: Path, video_id: str, cleanup_audio: bool = True
    ) -> Transcript:
        """Transcribe a single video file.

        Args:
            video_path: Path to video file
            video_id: Video identifier
            cleanup_audio: Delete audio file after transcription

        Returns:
            Transcript object

        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If transcription fails
        """
        logger.info(f"Transcribing video: {video_path.name}")

        try:
            # Extract audio
            audio_path = self.audio_extractor.extract(video_path)

            # Transcribe audio
            transcript = self.whisper_service.transcribe(
                audio_path=audio_path,
                video_id=video_id,
                include_timestamps=self.include_timestamps,
            )

            # Cleanup audio file if requested
            if cleanup_audio and audio_path.exists():
                audio_path.unlink()
                logger.debug(f"Cleaned up audio file: {audio_path}")

            return transcript

        except Exception as e:
            logger.error(f"Failed to transcribe {video_path}: {e}")
            raise

    def transcribe_batch(
        self,
        video_files: List[Tuple[Path, str]],
        show_progress: bool = True,
        cleanup_audio: bool = True,
    ) -> List[Transcript]:
        """Transcribe multiple video files concurrently with resume capability.

        Args:
            video_files: List of (video_path, video_id) tuples
            show_progress: Show progress bar
            cleanup_audio: Delete audio files after transcription

        Returns:
            List of Transcript objects
        """
        logger.info(f"Starting batch transcription of {len(video_files)} videos")

        transcripts = []
        failed_count = 0

        # Initialize progress tracker if resume enabled
        tracker = None
        files_to_process = video_files

        if self.enable_resume:
            # Create or load progress tracker
            item_ids = [video_id for _, video_id in video_files]
            tracker = ProgressTracker.create_or_load(
                stage="transcription",
                file_path=self.progress_file,
                item_ids=item_ids,
            )

            # Get resumable items
            resumable_ids = set(tracker.get_resumable_items())

            # Filter videos to only process resumable ones
            files_to_process = [
                (path, vid) for path, vid in video_files if vid in resumable_ids
            ]

            if len(files_to_process) < len(video_files):
                already_done = len(video_files) - len(files_to_process)
                logger.info(
                    f"Resuming transcription: {already_done} already completed, "
                    f"{len(files_to_process)} remaining"
                )

        # Create progress bar
        progress_bar = None
        if show_progress:
            progress_bar = tqdm(
                total=len(files_to_process),
                desc="Transcribing videos",
                unit="video",
                dynamic_ncols=True,
            )

        try:
            # Process videos concurrently
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all transcription tasks
                future_to_video = {
                    executor.submit(
                        self.transcribe_video,
                        video_path,
                        video_id,
                        cleanup_audio,
                    ): (video_path, video_id)
                    for video_path, video_id in files_to_process
                }

                # Process completed transcriptions
                for future in as_completed(future_to_video):
                    video_path, video_id = future_to_video[future]

                    try:
                        # Mark as in progress
                        if tracker:
                            tracker.start_item(video_id)
                            tracker.save(self.progress_file)

                        transcript = future.result()
                        transcripts.append(transcript)

                        # Mark as complete
                        if tracker:
                            tracker.complete_item(
                                video_id,
                                {
                                    "language": transcript.language,
                                    "word_count": transcript.word_count,
                                },
                            )
                            tracker.save(self.progress_file)

                        if progress_bar:
                            progress_bar.set_postfix_str(
                                f"✓ {video_path.name} ({transcript.language})"
                            )
                            progress_bar.update(1)

                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Transcription failed for {video_path}: {e}")

                        # Mark as failed
                        if tracker:
                            tracker.fail_item(video_id, str(e))
                            tracker.save(self.progress_file)

                        if progress_bar:
                            progress_bar.set_postfix_str(f"✗ {video_path.name}")
                            progress_bar.update(1)

        finally:
            if progress_bar:
                progress_bar.close()

            # Mark stage as complete
            if tracker:
                tracker.complete()
                tracker.save(self.progress_file)
                logger.info(f"Progress saved to {self.progress_file}")

        logger.info(
            f"Batch transcription complete: {len(transcripts)} successful, "
            f"{failed_count} failed"
        )

        return transcripts

    def save_transcripts(
        self, transcripts: List[Transcript], output_dir: Path
    ) -> None:
        """Save transcripts to JSON files.

        Args:
            transcripts: List of Transcript objects
            output_dir: Output directory for transcript files
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        for transcript in transcripts:
            output_path = output_dir / f"{transcript.video_id}.json"

            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(transcript.model_dump(), f, indent=2, default=str)

                logger.debug(f"Saved transcript: {output_path}")

            except Exception as e:
                logger.error(f"Failed to save transcript {transcript.video_id}: {e}")

        logger.info(f"Saved {len(transcripts)} transcripts to {output_dir}")

    def load_transcript(self, transcript_path: Path) -> Transcript:
        """Load transcript from JSON file.

        Args:
            transcript_path: Path to transcript JSON file

        Returns:
            Transcript object
        """
        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return Transcript(**data)

        except Exception as e:
            logger.error(f"Failed to load transcript from {transcript_path}: {e}")
            raise

    def load_transcripts(self, transcript_dir: Path) -> List[Transcript]:
        """Load all transcripts from directory.

        Args:
            transcript_dir: Directory containing transcript JSON files

        Returns:
            List of Transcript objects
        """
        transcripts = []

        for json_file in transcript_dir.glob("*.json"):
            try:
                transcript = self.load_transcript(json_file)
                transcripts.append(transcript)
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")

        logger.info(f"Loaded {len(transcripts)} transcripts from {transcript_dir}")
        return transcripts


def get_video_files_from_directory(video_dir: Path) -> List[Tuple[Path, str]]:
    """Get list of video files with their IDs from directory.

    Args:
        video_dir: Directory containing video files

    Returns:
        List of (video_path, video_id) tuples
    """
    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    video_files = []

    for video_path in video_dir.iterdir():
        if video_path.suffix.lower() in video_extensions:
            # Extract video ID from filename (assumes format: {video_id}_{shortcode}.mp4)
            video_id = video_path.stem.split("_")[0]
            video_files.append((video_path, video_id))

    logger.info(f"Found {len(video_files)} video files in {video_dir}")
    return video_files
