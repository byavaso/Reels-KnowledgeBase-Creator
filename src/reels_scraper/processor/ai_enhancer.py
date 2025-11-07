"""AI enhancement for content summarization and topic extraction."""

from typing import Dict, List

import google.generativeai as genai

from ..logger import get_logger

logger = get_logger(__name__)


class AIEnhancer:
    """Enhance content using Google Gemini for summarization and topic extraction."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        max_summary_length: int = 500,
    ):
        """Initialize AI enhancer.

        Args:
            api_key: Google API key
            model: Gemini model to use
            max_summary_length: Maximum summary length in words
        """
        self.model_name = model
        self.max_summary_length = max_summary_length

        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

        logger.debug(f"AI enhancer initialized: {model}")

    def generate_summary(self, transcript_text: str, language: str = "en") -> str:
        """Generate executive summary from transcript.

        Args:
            transcript_text: Full transcript text
            language: Language code for output

        Returns:
            Generated summary text
        """
        logger.info(f"Generating summary (max {self.max_summary_length} words)")

        try:
            # Build prompt
            prompt = f"""Please provide a concise executive summary of the following video transcript.

Language: {language}
Maximum length: {self.max_summary_length} words

Focus on:
- Main topic and purpose
- Key points discussed
- Important conclusions or takeaways

Transcript:
{transcript_text}

Provide the summary in the same language as the transcript."""

            # Generate summary
            response = self.model.generate_content(prompt)
            summary = response.text.strip()

            word_count = len(summary.split())
            logger.info(f"Summary generated ({word_count} words)")

            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return "Summary generation failed"

    def extract_key_points(self, transcript_text: str, max_points: int = 5) -> List[str]:
        """Extract key takeaways from transcript.

        Args:
            transcript_text: Full transcript text
            max_points: Maximum number of key points

        Returns:
            List of key points
        """
        logger.info(f"Extracting up to {max_points} key points")

        try:
            prompt = f"""Extract the {max_points} most important key takeaways from this video transcript.

Provide them as a bulleted list (one point per line, starting with "-").
Be concise and specific.

Transcript:
{transcript_text}

Key takeaways:"""

            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Parse bullet points
            key_points = []
            for line in text.split("\n"):
                line = line.strip()
                # Remove common bullet point markers
                for marker in ["-", "*", "•", "·"]:
                    if line.startswith(marker):
                        line = line[1:].strip()
                        break

                if line and len(key_points) < max_points:
                    key_points.append(line)

            logger.info(f"Extracted {len(key_points)} key points")
            return key_points

        except Exception as e:
            logger.error(f"Failed to extract key points: {e}")
            return []

    def extract_topics(self, transcript_text: str, max_topics: int = 5) -> List[str]:
        """Extract main topics/tags from transcript.

        Args:
            transcript_text: Full transcript text
            max_topics: Maximum number of topics

        Returns:
            List of topic tags
        """
        logger.info(f"Extracting up to {max_topics} topics")

        try:
            prompt = f"""Identify the {max_topics} main topics or themes in this video transcript.

Provide them as simple hashtags (e.g., #technology, #education).
One topic per line.

Transcript:
{transcript_text}

Topics:"""

            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Parse topics
            topics = []
            for line in text.split("\n"):
                line = line.strip()

                # Clean up topic
                if line:
                    # Remove # if present
                    topic = line.lstrip("#").strip()
                    # Convert to lowercase and remove spaces
                    topic = topic.lower().replace(" ", "_")

                    if topic and len(topics) < max_topics:
                        topics.append(topic)

            logger.info(f"Extracted {len(topics)} topics: {', '.join(topics)}")
            return topics

        except Exception as e:
            logger.error(f"Failed to extract topics: {e}")
            return []

    def enhance_content(
        self, transcript_text: str, language: str = "en"
    ) -> Dict[str, any]:
        """Perform complete content enhancement.

        Args:
            transcript_text: Full transcript text
            language: Language code

        Returns:
            Dictionary with summary, key_points, and topics
        """
        logger.info("Performing complete content enhancement")

        try:
            # Generate all enhancements
            summary = self.generate_summary(transcript_text, language)
            key_points = self.extract_key_points(transcript_text)
            topics = self.extract_topics(transcript_text)

            return {"summary": summary, "key_points": key_points, "topics": topics}

        except Exception as e:
            logger.error(f"Content enhancement failed: {e}")
            return {
                "summary": "Enhancement failed",
                "key_points": [],
                "topics": [],
            }
