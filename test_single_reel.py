"""Test script for single Reels transcription and markdown generation."""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from reels_scraper.transcription.local_whisper import LocalWhisperService
from reels_scraper.processor.markdown_generator import MarkdownGenerator
from reels_scraper.models import ReelMetadata

# Transcribe video
print("=== Transcribing video ===")
whisper_service = LocalWhisperService(model_name='base')
transcript = whisper_service.transcribe(
    Path('output/single_reel.mp4'),
    'DQkZsveDqvT'
)

print(f"[OK] Transcribed: {transcript.word_count} words, {len(transcript.segments)} segments")
print(f"  Language: {transcript.language}")

# Create metadata for the Reel
from datetime import datetime

reel_metadata = ReelMetadata(
    video_id='DQkZsveDqvT',
    shortcode='DQkZsveDqvT',
    url='https://www.instagram.com/reel/DQkZsveDqvT/',
    caption='',
    timestamp=datetime.now(),
    view_count=0,
    like_count=0,
    comment_count=0,
    video_url='https://www.instagram.com/reel/DQkZsveDqvT/',
    thumbnail_url='',
    duration=transcript.duration,
    owner_username='brendankane',
)

# Enhance with AI
print("\n=== Enhancing with Gemini ===")
from reels_scraper.processor.ai_enhancer import AIEnhancer
import os

# Get API key from environment
gemini_api_key = os.getenv("GOOGLE_API_KEY")
if not gemini_api_key:
    print("[ERROR] GOOGLE_API_KEY not found in environment")
    exit(1)

enhancer = AIEnhancer(api_key=gemini_api_key)
enhancement = enhancer.enhance_content(transcript.text, transcript.language)
print(f"[OK] AI enhancement complete")
print(f"  Summary: {enhancement['summary'][:100]}...")
print(f"  Key points: {len(enhancement['key_points'])}")
print(f"  Topics: {', '.join(enhancement['topics'])}")

# Generate markdown
print("\n=== Generating markdown ===")
generator = MarkdownGenerator()
report = generator.generate(
    transcript=transcript,
    summary=enhancement['summary'],
    key_points=enhancement['key_points'],
    topics=enhancement['topics'],
    reel=reel_metadata,
)

# Save report
output_path = generator.save_report(report, Path('output'))
print(f"[OK] Markdown generated: {output_path}")

# Show preview
print(f"\n=== Preview ===")
print(report.content[:500])
print("...")
