"""OpenAI Whisper API integration for transcription."""

from pathlib import Path
from typing import Optional

import openai

from ..logger import get_logger
from ..models import Transcript, TranscriptSegment

logger = get_logger(__name__)


class WhisperService:
    """Service for transcribing audio using OpenAI Whisper API."""

    def __init__(
        self,
        api_key: str,
        model: str = "whisper-1",
        language: Optional[str] = None,
    ):
        """Initialize Whisper service.

        Args:
            api_key: OpenAI API key
            model: Whisper model to use
            language: Language code (None for auto-detection)
        """
        self.api_key = api_key
        self.model = model
        self.language = language
        self.client = openai.OpenAI(api_key=api_key)

        logger.debug(f"Whisper service initialized: model={model}, language={language}")

    def transcribe(
        self,
        audio_path: Path,
        video_id: str,
        include_timestamps: bool = True,
    ) -> Transcript:
        """Transcribe audio file using Whisper API.

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

        logger.info(f"Transcribing {audio_path.name} using Whisper API")

        try:
            # Open audio file
            with open(audio_path, "rb") as audio_file:
                # Call Whisper API
                kwargs = {
                    "file": audio_file,
                    "model": self.model,
                    "response_format": "verbose_json" if include_timestamps else "text",
                }

                if self.language and self.language != "auto":
                    kwargs["language"] = self.language

                response = self.client.audio.transcriptions.create(**kwargs)

            # Parse response
            if include_timestamps:
                # Extract text and segments
                text = response.text
                language = response.language if hasattr(response, "language") else "unknown"
                duration = response.duration if hasattr(response, "duration") else 0.0

                segments = []
                if hasattr(response, "segments"):
                    for seg in response.segments:
                        segments.append(
                            TranscriptSegment(
                                start_time=seg["start"],
                                end_time=seg["end"],
                                text=seg["text"].strip(),
                                speaker=None,
                            )
                        )

                # Count words
                word_count = len(text.split())

            else:
                # Simple text response
                text = response if isinstance(response, str) else response.text
                language = self.language or "unknown"
                duration = 0.0
                segments = []
                word_count = len(text.split())

            transcript = Transcript(
                video_id=video_id,
                text=text,
                language=language,
                segments=segments,
                confidence=0.0,  # Whisper API doesn't provide confidence
                duration=duration,
                word_count=word_count,
                service="openai-whisper",
                model=self.model,
            )

            logger.info(
                f"Transcription complete: {word_count} words, "
                f"{len(segments)} segments, language={language}"
            )

            return transcript

        except openai.OpenAIError as e:
            error_msg = f"Whisper API error: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

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
