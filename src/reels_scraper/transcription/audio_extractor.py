"""Audio extraction from video files using ffmpeg."""

import subprocess
from pathlib import Path
from typing import Optional

from ..logger import get_logger

logger = get_logger(__name__)


class AudioExtractor:
    """Extract audio from video files using ffmpeg."""

    def __init__(self, audio_format: str = "mp3", sample_rate: int = 16000):
        """Initialize audio extractor.

        Args:
            audio_format: Output audio format (mp3, wav)
            sample_rate: Audio sample rate in Hz (16000 recommended for Whisper)
        """
        self.audio_format = audio_format
        self.sample_rate = sample_rate

        logger.debug(f"Audio extractor initialized: {audio_format}, {sample_rate}Hz")

    def extract(self, video_path: Path, output_path: Optional[Path] = None) -> Path:
        """Extract audio from video file.

        Args:
            video_path: Path to input video file
            output_path: Optional path to output audio file

        Returns:
            Path to extracted audio file

        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If ffmpeg extraction fails
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Generate output path if not provided
        if not output_path:
            output_path = video_path.with_suffix(f".{self.audio_format}")

        logger.debug(f"Extracting audio from {video_path} to {output_path}")

        try:
            # Build ffmpeg command
            cmd = [
                "ffmpeg",
                "-i",
                str(video_path),
                "-vn",  # No video
                "-acodec",
                "libmp3lame" if self.audio_format == "mp3" else "pcm_s16le",
                "-ar",
                str(self.sample_rate),  # Sample rate
                "-ac",
                "1",  # Mono audio
                "-y",  # Overwrite output
                str(output_path),
            ]

            # Run ffmpeg
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )

            if not output_path.exists():
                raise RuntimeError("Audio extraction completed but output file not found")

            file_size = output_path.stat().st_size
            logger.info(
                f"Audio extracted: {output_path.name} ({file_size / 1024:.2f} KB)"
            )

            return output_path

        except subprocess.CalledProcessError as e:
            error_msg = f"ffmpeg failed: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise

    def extract_batch(
        self, video_paths: list[Path], output_dir: Optional[Path] = None
    ) -> list[Path]:
        """Extract audio from multiple video files.

        Args:
            video_paths: List of video file paths
            output_dir: Optional directory for output audio files

        Returns:
            List of extracted audio file paths
        """
        audio_paths = []

        for video_path in video_paths:
            try:
                if output_dir:
                    output_path = output_dir / f"{video_path.stem}.{self.audio_format}"
                    output_dir.mkdir(parents=True, exist_ok=True)
                else:
                    output_path = None

                audio_path = self.extract(video_path, output_path)
                audio_paths.append(audio_path)

            except Exception as e:
                logger.error(f"Failed to extract audio from {video_path}: {e}")
                # Continue with next file

        return audio_paths

    @staticmethod
    def check_ffmpeg_installed() -> bool:
        """Check if ffmpeg is installed and available.

        Returns:
            True if ffmpeg is available
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
