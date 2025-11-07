"""Content processor for generating markdown reports."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

from tqdm import tqdm

from ..logger import get_logger
from ..models import MarkdownReport, ReelMetadata, Transcript
from ..progress import ProgressTracker
from .ai_enhancer import AIEnhancer
from .markdown_generator import MarkdownGenerator, load_reel_metadata_from_json

logger = get_logger(__name__)


class ContentProcessor:
    """Process transcripts into enhanced markdown reports."""

    def __init__(
        self,
        google_api_key: str,
        ai_model: str = "gemini-2.0-flash-exp",
        template: str = "default",
        max_summary_length: int = 500,
        extract_topics: bool = True,
        generate_summary: bool = True,
        enable_resume: bool = True,
        progress_file: Optional[Path] = None,
        output_dir: Path = Path("./output/markdown"),
    ):
        """Initialize content processor.

        Args:
            google_api_key: Google API key for Gemini
            ai_model: AI model to use
            template: Markdown template name
            max_summary_length: Maximum summary length in words
            extract_topics: Whether to extract topics
            generate_summary: Whether to generate AI summary
            enable_resume: Enable resume capability with progress tracking
            progress_file: Custom path for progress file
            output_dir: Output directory (for default progress file path)
        """
        self.ai_enhancer = AIEnhancer(
            api_key=google_api_key,
            model=ai_model,
            max_summary_length=max_summary_length,
        )
        self.markdown_generator = MarkdownGenerator(template=template)
        self.extract_topics = extract_topics
        self.generate_summary = generate_summary
        self.enable_resume = enable_resume
        self.progress_file = progress_file or (output_dir / ".processing_progress.json")

        logger.info(
            f"Content processor initialized: {ai_model}, template={template}, "
            f"summary={generate_summary}, topics={extract_topics}, resume={enable_resume}"
        )

    def process_transcript(
        self,
        transcript: Transcript,
        reel: Optional[ReelMetadata] = None,
    ) -> MarkdownReport:
        """Process single transcript into markdown report.

        Args:
            transcript: Transcript object
            reel: Optional reel metadata

        Returns:
            MarkdownReport object
        """
        logger.info(f"Processing transcript for video {transcript.video_id}")

        try:
            # Generate enhancements
            if self.generate_summary or self.extract_topics:
                enhancements = self.ai_enhancer.enhance_content(
                    transcript.text, transcript.language
                )
                summary = enhancements["summary"] if self.generate_summary else ""
                key_points = enhancements["key_points"]
                topics = enhancements["topics"] if self.extract_topics else []
            else:
                summary = ""
                key_points = []
                topics = []

            # Generate markdown report
            report = self.markdown_generator.generate(
                transcript=transcript,
                summary=summary,
                key_points=key_points,
                topics=topics,
                reel=reel,
            )

            logger.info(f"Processed transcript: {report.title}")
            return report

        except Exception as e:
            logger.error(f"Failed to process transcript {transcript.video_id}: {e}")
            raise

    def process_batch(
        self,
        transcripts: List[Transcript],
        reels_metadata: Optional[Dict[str, ReelMetadata]] = None,
        show_progress: bool = True,
    ) -> List[MarkdownReport]:
        """Process multiple transcripts with resume capability.

        Args:
            transcripts: List of Transcript objects
            reels_metadata: Optional dictionary mapping video_id to ReelMetadata
            show_progress: Show progress bar

        Returns:
            List of MarkdownReport objects
        """
        logger.info(f"Starting batch processing of {len(transcripts)} transcripts")

        reports = []
        failed_count = 0

        # Initialize progress tracker if resume enabled
        tracker = None
        transcripts_to_process = transcripts

        if self.enable_resume:
            # Create or load progress tracker
            item_ids = [t.video_id for t in transcripts]
            tracker = ProgressTracker.create_or_load(
                stage="processing",
                file_path=self.progress_file,
                item_ids=item_ids,
            )

            # Get resumable items
            resumable_ids = set(tracker.get_resumable_items())

            # Filter transcripts to only process resumable ones
            transcripts_to_process = [t for t in transcripts if t.video_id in resumable_ids]

            if len(transcripts_to_process) < len(transcripts):
                already_done = len(transcripts) - len(transcripts_to_process)
                logger.info(
                    f"Resuming processing: {already_done} already completed, "
                    f"{len(transcripts_to_process)} remaining"
                )

        # Create progress bar
        progress_bar = None
        if show_progress:
            progress_bar = tqdm(
                total=len(transcripts_to_process),
                desc="Processing transcripts",
                unit="transcript",
                dynamic_ncols=True,
            )

        try:
            # Process transcripts sequentially (Gemini API has rate limits)
            for transcript in transcripts_to_process:
                try:
                    # Mark as in progress
                    if tracker:
                        tracker.start_item(transcript.video_id)
                        tracker.save(self.progress_file)

                    reel = None
                    if reels_metadata:
                        reel = reels_metadata.get(transcript.video_id)

                    report = self.process_transcript(transcript, reel)
                    reports.append(report)

                    # Mark as complete
                    if tracker:
                        tracker.complete_item(
                            transcript.video_id,
                            {"title": report.title, "topics": report.topics},
                        )
                        tracker.save(self.progress_file)

                    if progress_bar:
                        progress_bar.set_postfix_str(f"✓ {transcript.video_id[:8]}")
                        progress_bar.update(1)

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to process transcript {transcript.video_id}: {e}")

                    # Mark as failed
                    if tracker:
                        tracker.fail_item(transcript.video_id, str(e))
                        tracker.save(self.progress_file)

                    if progress_bar:
                        progress_bar.set_postfix_str(f"✗ {transcript.video_id[:8]}")
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
            f"Batch processing complete: {len(reports)} successful, {failed_count} failed"
        )

        return reports

    def save_reports(
        self, reports: List[MarkdownReport], output_dir: Path
    ) -> List[Path]:
        """Save markdown reports to files.

        Args:
            reports: List of MarkdownReport objects
            output_dir: Output directory

        Returns:
            List of saved file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for report in reports:
            try:
                path = self.markdown_generator.save_report(report, output_dir)
                saved_paths.append(path)
            except Exception as e:
                logger.error(f"Failed to save report for {report.video_id}: {e}")

        logger.info(f"Saved {len(saved_paths)} markdown reports to {output_dir}")
        return saved_paths


def load_transcripts_from_directory(transcript_dir: Path) -> List[Transcript]:
    """Load all transcripts from directory.

    Args:
        transcript_dir: Directory containing transcript JSON files

    Returns:
        List of Transcript objects
    """
    import json

    transcripts = []

    for json_file in transcript_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            transcript = Transcript(**data)
            transcripts.append(transcript)

        except Exception as e:
            logger.error(f"Failed to load transcript from {json_file}: {e}")

    logger.info(f"Loaded {len(transcripts)} transcripts from {transcript_dir}")
    return transcripts
