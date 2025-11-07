"""Local Whisper model for transcription."""

from pathlib import Path
from typing import Optional

import whisper

from ..logger import get_logger
from ..models import Transcript, TranscriptSegment

logger = get_logger(__name__)


class LocalWhisperService:
    """Service for transcribing audio using local Whisper model."""

    def __init__(
        self,
        model_name: str = "base",
        language: Optional[str] = None,
        device: Optional[str] = None,
    ):
        """Initialize local Whisper service.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            language: Language code (None for auto-detection)
            device: Device to run on (None for auto, 'cpu' or 'cuda')
        """
        self.model_name = model_name
        self.language = language
        self.device = device

        logger.info(f"Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name, device=device)
        logger.info(f"Whisper model loaded successfully")

    def transcribe(
        self,
        audio_path: Path,
        video_id: str,
        include_timestamps: bool = True,
    ) -> Transcript:
        """Transcribe audio file using local Whisper model.

        Args:
            audio_path: Path to audio file
            video_id: Video identifier
            include_timestamps: Include word-level timestamps

        Returns:
            Transcript object

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Transcribing {audio_path.name} using local Whisper model")

        try:
            # Transcribe with Whisper
            kwargs = {
                "verbose": False,
            }

            if self.language and self.language != "auto":
                kwargs["language"] = self.language

            result = self.model.transcribe(str(audio_path), **kwargs)

            # Extract data
            text = result["text"]
            language = result.get("language", "unknown")

            # Parse segments
            segments = []
            if include_timestamps and "segments" in result:
                for seg in result["segments"]:
                    segments.append(
                        TranscriptSegment(
                            start_time=seg["start"],
                            end_time=seg["end"],
                            text=seg["text"].strip(),
                            speaker=None,
                        )
                    )

            # Calculate duration
            duration = segments[-1].end_time if segments else 0.0

            # Count words
            word_count = len(text.split())

            transcript = Transcript(
                video_id=video_id,
                text=text,
                language=language,
                segments=segments,
                confidence=0.0,  # Local Whisper doesn't provide confidence
                duration=duration,
                word_count=word_count,
                service="local-whisper",
                model=self.model_name,
            )

            logger.info(
                f"Transcription complete: {word_count} words, "
                f"{len(segments)} segments, language={language}"
            )

            return transcript

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Local Whisper transcription error: {e}") from e

    def transcribe_batch(
        self,
        audio_paths: list[tuple[Path, str]],
        include_timestamps: bool = True,
    ) -> list[Transcript]:
        """Transcribe multiple audio files.

        Args:
            audio_paths: List of (audio_path, video_id) tuples
            include_timestamps: Include timestamps in transcripts

        Returns:
            List of Transcript objects
        """
        transcripts = []

        for audio_path, video_id in audio_paths:
            try:
                transcript = self.transcribe(audio_path, video_id, include_timestamps)
                transcripts.append(transcript)
            except Exception as e:
                logger.error(f"Failed to transcribe {audio_path}: {e}")
                # Continue with next file

        return transcripts
