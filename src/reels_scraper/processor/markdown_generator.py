"""Markdown report generator using Jinja2 templates."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template

from ..logger import get_logger
from ..models import MarkdownReport, ReelMetadata, Transcript

logger = get_logger(__name__)


class MarkdownGenerator:
    """Generate markdown reports from transcripts and metadata."""

    def __init__(self, template_name: str = "default"):
        """Initialize markdown generator.

        Args:
            template_name: Name of template to use
        """
        self.template_name = template_name

        # Set up Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

        logger.debug(f"Markdown generator initialized with template: {template_name}")

    def _load_template(self) -> Template:
        """Load Jinja2 template.

        Returns:
            Jinja2 Template object
        """
        template_file = f"{self.template_name}.md.j2"

        try:
            template = self.env.get_template(template_file)
            return template
        except Exception as e:
            logger.error(f"Failed to load template {template_file}: {e}")
            raise

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def _create_title(
        self, reel: Optional[ReelMetadata], transcript: Transcript
    ) -> str:
        """Create title for markdown report.

        Args:
            reel: Optional reel metadata
            transcript: Transcript object

        Returns:
            Generated title
        """
        if reel and reel.caption:
            # Use first line of caption as title
            title = reel.caption.split("\n")[0].strip()
            # Limit length
            if len(title) > 100:
                title = title[:97] + "..."
            return title
        else:
            # Fallback to generic title
            return f"Video Transcript {transcript.video_id[:8]}"

    def _create_filename(
        self, reel: Optional[ReelMetadata], transcript: Transcript
    ) -> str:
        """Create filename for markdown report.

        Args:
            reel: Optional reel metadata
            transcript: Transcript object

        Returns:
            Generated filename
        """
        # Use date from reel metadata
        if reel:
            date_str = reel.timestamp.strftime("%Y%m%d")
            # Clean shortcode for filename
            shortcode = reel.shortcode.replace("/", "_")
            return f"{date_str}_{shortcode}.md"
        else:
            # Fallback to video ID
            return f"{transcript.video_id}.md"

    def generate(
        self,
        transcript: Transcript,
        summary: str,
        key_points: list[str],
        topics: list[str],
        reel: Optional[ReelMetadata] = None,
    ) -> MarkdownReport:
        """Generate markdown report.

        Args:
            transcript: Transcript object
            summary: AI-generated summary
            key_points: List of key takeaways
            topics: List of topic tags
            reel: Optional reel metadata

        Returns:
            MarkdownReport object
        """
        logger.info(f"Generating markdown report for video {transcript.video_id}")

        try:
            # Load template
            template = self._load_template()

            # Create title and filename
            title = self._create_title(reel, transcript)
            filename = self._create_filename(reel, transcript)

            # Prepare metadata
            metadata = {
                "profile": reel.owner_username if reel else "unknown",
                "date": reel.timestamp.strftime("%Y-%m-%d") if reel else "unknown",
                "duration": self._format_duration(transcript.duration),
                "url": reel.url if reel else "N/A",
                "views": f"{reel.view_count:,}" if reel else None,
                "likes": f"{reel.like_count:,}" if reel else None,
            }

            # Get formatted transcript
            formatted_transcript = transcript.get_formatted_transcript()

            # Render template
            content = template.render(
                title=title,
                metadata=metadata,
                summary=summary,
                formatted_transcript=formatted_transcript,
                key_points=key_points,
                topics=topics,
                language=transcript.language,
                word_count=f"{transcript.word_count:,}",
                service=transcript.service,
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            # Create report
            report = MarkdownReport(
                video_id=transcript.video_id,
                title=title,
                content=content,
                summary=summary,
                topics=topics,
                key_points=key_points,
                metadata=metadata,
                file_path=None,  # Will be set when saved
            )

            logger.info(f"Markdown report generated: {filename}")
            return report

        except Exception as e:
            logger.error(f"Failed to generate markdown report: {e}")
            raise

    def save_report(self, report: MarkdownReport, output_dir: Path) -> Path:
        """Save markdown report to file.

        Args:
            report: MarkdownReport object
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"{report.video_id}.md"
        if report.metadata.get("date"):
            date_str = report.metadata["date"].replace("-", "")
            filename = f"{date_str}_{report.video_id[:8]}.md"

        output_path = output_dir / filename

        try:
            # Save markdown content
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report.content)

            logger.info(f"Markdown report saved to {output_path}")

            # Update report with file path
            report.file_path = output_path

            return output_path

        except Exception as e:
            logger.error(f"Failed to save markdown report: {e}")
            raise


def load_reel_metadata_from_json(json_path: Path) -> Dict[str, ReelMetadata]:
    """Load reel metadata from JSON file into dictionary.

    Args:
        json_path: Path to reels_list.json file

    Returns:
        Dictionary mapping video_id to ReelMetadata
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        reels_dict = {}
        for reel_data in data:
            reel = ReelMetadata(**reel_data)
            reels_dict[reel.video_id] = reel

        logger.info(f"Loaded {len(reels_dict)} reel metadata entries")
        return reels_dict

    except Exception as e:
        logger.error(f"Failed to load reel metadata: {e}")
        return {}
