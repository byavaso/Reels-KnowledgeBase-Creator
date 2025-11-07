"""Knowledge base builder and organizer."""

import json
import re
import shutil
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..logger import get_logger

logger = get_logger(__name__)


class KnowledgeBaseBuilder:
    """Build and organize knowledge base from markdown files."""

    def __init__(
        self,
        markdown_dir: Path,
        output_dir: Path,
        organize_by_topic: bool = True,
        create_index: bool = True,
    ):
        """Initialize knowledge base builder.

        Args:
            markdown_dir: Directory containing markdown files
            output_dir: Output directory for organized knowledge base
            organize_by_topic: Whether to organize files by topics
            create_index: Whether to create master index.md
        """
        self.markdown_dir = Path(markdown_dir)
        self.output_dir = Path(output_dir)
        self.organize_by_topic = organize_by_topic
        self.create_index = create_index

        # Data structures for organization
        self.markdown_files: List[Path] = []
        self.topics_map: Dict[str, List[Path]] = defaultdict(list)
        self.metadata_map: Dict[Path, Dict] = {}

        logger.info(f"Knowledge base builder initialized")
        logger.info(f"Source: {self.markdown_dir}")
        logger.info(f"Output: {self.output_dir}")

    def _extract_metadata_from_markdown(self, md_file: Path) -> Dict:
        """Extract metadata from markdown file.

        Args:
            md_file: Path to markdown file

        Returns:
            Dictionary with metadata (title, profile, topics, etc.)
        """
        try:
            content = md_file.read_text(encoding="utf-8")

            metadata = {
                "file": md_file.name,
                "path": md_file,
                "title": "",
                "profile": "",
                "url": "",
                "topics": [],
                "word_count": 0,
                "language": "",
            }

            # Extract title (first # heading)
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if title_match:
                metadata["title"] = title_match.group(1).strip()

            # Extract profile
            profile_match = re.search(r"\*\*Profile\*\*:\s*@(\w+)", content)
            if profile_match:
                metadata["profile"] = profile_match.group(1).strip()

            # Extract URL
            url_match = re.search(r"\*\*URL\*\*:\s*\[([^\]]+)\]\(([^)]+)\)", content)
            if url_match:
                metadata["url"] = url_match.group(2).strip()

            # Extract topics (looking for ## Topics section)
            topics_section = re.search(
                r"##\s+Topics\s*\n\s*((?:#\w+\s*)+)", content, re.IGNORECASE
            )
            if topics_section:
                topics_text = topics_section.group(1)
                # Extract hashtags
                topics = re.findall(r"#(\w+)", topics_text)
                metadata["topics"] = [t.lower() for t in topics]

            # Extract word count
            wc_match = re.search(r"\*\*Word Count\*\*:\s*(\d+)", content)
            if wc_match:
                metadata["word_count"] = int(wc_match.group(1))

            # Extract language
            lang_match = re.search(r"\*\*Language\*\*:\s*(\w+)", content)
            if lang_match:
                metadata["language"] = lang_match.group(1).strip()

            return metadata

        except Exception as e:
            logger.error(f"Failed to extract metadata from {md_file.name}: {e}")
            return {
                "file": md_file.name,
                "path": md_file,
                "title": md_file.stem,
                "topics": [],
            }

    def scan_markdown_files(self) -> None:
        """Scan markdown directory and extract metadata."""
        logger.info(f"Scanning markdown files in {self.markdown_dir}")

        if not self.markdown_dir.exists():
            raise FileNotFoundError(f"Markdown directory not found: {self.markdown_dir}")

        # Find all markdown files
        self.markdown_files = sorted(self.markdown_dir.glob("*.md"))

        if not self.markdown_files:
            logger.warning(f"No markdown files found in {self.markdown_dir}")
            return

        logger.info(f"Found {len(self.markdown_files)} markdown files")

        # Extract metadata from each file
        for md_file in self.markdown_files:
            metadata = self._extract_metadata_from_markdown(md_file)
            self.metadata_map[md_file] = metadata

            # Build topics map
            if metadata["topics"]:
                for topic in metadata["topics"]:
                    self.topics_map[topic].append(md_file)
            else:
                # Files without topics go to "uncategorized"
                self.topics_map["uncategorized"].append(md_file)

        logger.info(f"Extracted metadata from {len(self.metadata_map)} files")
        logger.info(f"Found {len(self.topics_map)} unique topics")

    def organize_by_topics(self) -> None:
        """Organize markdown files into topic-based folders."""
        if not self.organize_by_topic:
            logger.info("Topic organization disabled, skipping")
            return

        logger.info("Organizing files by topics")

        # Create topic directories and copy files
        for topic, files in self.topics_map.items():
            topic_dir = self.output_dir / topic
            topic_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Topic '{topic}': {len(files)} files")

            for md_file in files:
                dest_file = topic_dir / md_file.name
                shutil.copy2(md_file, dest_file)
                logger.debug(f"Copied {md_file.name} to {topic}/")

        logger.info(f"Organized {len(self.markdown_files)} files into {len(self.topics_map)} topics")

    def copy_flat_structure(self) -> None:
        """Copy all markdown files to output directory (flat structure)."""
        if self.organize_by_topic:
            logger.info("Using topic organization, skipping flat copy")
            return

        logger.info("Copying files to output directory (flat structure)")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        for md_file in self.markdown_files:
            dest_file = self.output_dir / md_file.name
            shutil.copy2(md_file, dest_file)
            logger.debug(f"Copied {md_file.name}")

        logger.info(f"Copied {len(self.markdown_files)} files")

    def generate_index(self) -> None:
        """Generate master index.md file."""
        if not self.create_index:
            logger.info("Index generation disabled, skipping")
            return

        logger.info("Generating master index.md")

        index_path = self.output_dir / "index.md"

        # Build index content
        lines = []
        lines.append("# Instagram Reels Knowledge Base\n")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**Total Reels**: {len(self.markdown_files)}\n")
        lines.append(f"**Topics**: {len(self.topics_map)}\n")
        lines.append("\n---\n\n")

        # Statistics
        total_words = sum(m["word_count"] for m in self.metadata_map.values())
        languages = set(m["language"] for m in self.metadata_map.values() if m["language"])
        profiles = set(m["profile"] for m in self.metadata_map.values() if m["profile"])

        lines.append("## Statistics\n\n")
        lines.append(f"- **Total Word Count**: {total_words:,}\n")
        lines.append(f"- **Languages**: {', '.join(languages) if languages else 'N/A'}\n")
        lines.append(f"- **Profiles**: {', '.join('@' + p for p in profiles)}\n")
        lines.append("\n---\n\n")

        # Topics overview
        if self.organize_by_topic and self.topics_map:
            lines.append("## Topics\n\n")
            for topic in sorted(self.topics_map.keys()):
                count = len(self.topics_map[topic])
                lines.append(f"- **{topic}** ({count} reels)\n")
            lines.append("\n---\n\n")

        # List all reels by topic
        if self.organize_by_topic:
            lines.append("## Reels by Topic\n\n")
            for topic in sorted(self.topics_map.keys()):
                lines.append(f"### {topic.title()}\n\n")

                files = self.topics_map[topic]
                for md_file in sorted(files, key=lambda f: self.metadata_map[f]["title"]):
                    metadata = self.metadata_map[md_file]
                    title = metadata["title"] or md_file.stem
                    profile = f"@{metadata['profile']}" if metadata["profile"] else ""
                    url = metadata["url"]
                    rel_path = f"{topic}/{md_file.name}"

                    lines.append(f"#### [{title}]({rel_path})\n")
                    if profile:
                        lines.append(f"**Profile**: {profile}  \n")
                    if url:
                        lines.append(f"**URL**: {url}  \n")
                    lines.append(f"**Word Count**: {metadata['word_count']}  \n")
                    lines.append("\n")

                lines.append("\n")
        else:
            # Flat structure - just list all files
            lines.append("## All Reels\n\n")
            for md_file in sorted(self.markdown_files, key=lambda f: self.metadata_map[f]["title"]):
                metadata = self.metadata_map[md_file]
                title = metadata["title"] or md_file.stem
                profile = f"@{metadata['profile']}" if metadata["profile"] else ""
                url = metadata["url"]

                lines.append(f"### [{title}]({md_file.name})\n")
                if profile:
                    lines.append(f"**Profile**: {profile}  \n")
                if url:
                    lines.append(f"**URL**: {url}  \n")
                lines.append(f"**Word Count**: {metadata['word_count']}  \n")
                if metadata["topics"]:
                    topics_str = ", ".join(f"#{t}" for t in metadata["topics"])
                    lines.append(f"**Topics**: {topics_str}  \n")
                lines.append("\n")

        # Write index file
        index_content = "".join(lines)
        index_path.write_text(index_content, encoding="utf-8")

        logger.info(f"Generated index.md at {index_path}")
        logger.info(f"Index contains {len(self.markdown_files)} reels across {len(self.topics_map)} topics")

    def build(self) -> None:
        """Execute complete knowledge base building workflow."""
        logger.info("Starting knowledge base building workflow")

        # Scan and analyze markdown files
        self.scan_markdown_files()

        if not self.markdown_files:
            logger.warning("No markdown files to process")
            return

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Organize files
        if self.organize_by_topic:
            self.organize_by_topics()
        else:
            self.copy_flat_structure()

        # Generate index
        if self.create_index:
            self.generate_index()

        logger.info(f"Knowledge base built successfully at {self.output_dir}")

    def create_stats_summary(self) -> Dict:
        """Create statistics summary.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_reels": len(self.markdown_files),
            "total_topics": len(self.topics_map),
            "total_words": sum(m["word_count"] for m in self.metadata_map.values()),
            "languages": list(set(m["language"] for m in self.metadata_map.values() if m["language"])),
            "profiles": list(set(m["profile"] for m in self.metadata_map.values() if m["profile"])),
            "topics_breakdown": {topic: len(files) for topic, files in self.topics_map.items()},
            "generated_at": datetime.now().isoformat(),
        }

        return stats

    def save_stats(self) -> None:
        """Save statistics to JSON file."""
        stats_file = self.output_dir / "stats.json"
        stats = self.create_stats_summary()

        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved statistics to {stats_file}")

    def create_zip_archive(self, zip_name: str = "knowledge-base.zip") -> Path:
        """Create ZIP archive of the knowledge base.

        Args:
            zip_name: Name of the ZIP file

        Returns:
            Path to created ZIP file
        """
        logger.info(f"Creating ZIP archive: {zip_name}")

        if not self.output_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {self.output_dir}")

        # ZIP file path (in parent directory of output_dir)
        zip_path = self.output_dir.parent / zip_name

        # Create ZIP archive
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Walk through output directory and add all files
            for file_path in self.output_dir.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path for archive
                    arcname = file_path.relative_to(self.output_dir.parent)
                    zipf.write(file_path, arcname)
                    logger.debug(f"Added to ZIP: {arcname}")

        # Get ZIP file size
        zip_size = zip_path.stat().st_size
        zip_size_mb = zip_size / (1024 * 1024)

        logger.info(f"ZIP archive created: {zip_path}")
        logger.info(f"ZIP size: {zip_size_mb:.2f} MB")

        return zip_path
