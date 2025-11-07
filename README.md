# Instagram Reels Knowledge Base Creator

A powerful Python CLI tool that transforms Instagram Reels into structured knowledge bases. Perfect for extracting valuable content from educational Instagram accounts and organizing it for AI tools like NotebookLM.

## Features

- 🎥 **Instagram Scraping**: Automatically discover and collect all Reels from any public Instagram profile
- ⬇️ **Video Download**: Concurrent downloading with retry logic and resume capability
- 🎤 **Transcription**: Convert speech to text using OpenAI Whisper API
- 🤖 **AI Enhancement**: Generate summaries and extract key topics using Google Gemini
- 📝 **Markdown Generation**: Create structured, NotebookLM-ready documentation
- 📚 **Knowledge Base**: Organize content with indexes, categories, and statistics

## Installation

### Prerequisites

- Python 3.10 or higher
- ffmpeg (for audio extraction)

### Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/reels-knowledge-base-creator.git
cd reels-knowledge-base-creator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Quick Start

### 1. Configure API Keys

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key
GOOGLE_API_KEY=your-google-gemini-api-key

# Optional
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
```

### 2. Run the Full Pipeline

```bash
# Process all Reels from an Instagram profile
reels-scraper full https://www.instagram.com/profile_name/

# Or with a username
reels-scraper full profile_name
```

### 3. Use Individual Commands

```bash
# Step 1: Scrape Instagram profile
reels-scraper scrape profile_name --output-dir ./output

# Step 2: Download videos
reels-scraper download --input-json ./output/reels_list.json --workers 3

# Step 3: Transcribe videos
reels-scraper transcribe --video-dir ./output/downloads

# Step 4: Generate markdown reports
reels-scraper generate --transcript-dir ./output/transcripts

# Step 5: Build knowledge base index
reels-scraper index --markdown-dir ./output/markdown
```

## Usage

### Full Pipeline

```bash
# Basic usage
reels-scraper full profile_name

# With custom config
reels-scraper full profile_name --config config.yaml

# Limit number of videos
reels-scraper full profile_name --limit 10

# Verbose output
reels-scraper full profile_name --verbose
```

### Scrape Command

```bash
# Scrape profile metadata and Reels list
reels-scraper scrape profile_name

# Limit number of Reels
reels-scraper scrape profile_name --limit 50

# Custom output directory
reels-scraper scrape profile_name --output-dir ./my-output
```

### Download Command

```bash
# Download videos from scraped metadata
reels-scraper download --input-json ./output/reels_list.json

# Use 5 concurrent workers
reels-scraper download --input-json ./output/reels_list.json --workers 5

# Skip already downloaded videos
reels-scraper download --input-json ./output/reels_list.json --skip-existing
```

### Transcribe Command

```bash
# Transcribe all videos in directory
reels-scraper transcribe --video-dir ./output/downloads

# Use specific language
reels-scraper transcribe --video-dir ./output/downloads --language tr

# Concurrent transcription
reels-scraper transcribe --video-dir ./output/downloads --workers 2
```

### Generate Command

```bash
# Generate markdown from transcripts
reels-scraper generate --transcript-dir ./output/transcripts

# Use custom template
reels-scraper generate --transcript-dir ./output/transcripts --template custom.j2
```

## Configuration

Create a `config.yaml` file for persistent settings:

```yaml
# Instagram settings
instagram:
  username: null  # Optional: for private profiles
  password: null  # Optional: for private profiles
  rate_limit_delay: 2  # Seconds between requests

# Download settings
download:
  max_workers: 3
  retry_count: 3
  output_dir: ./output/downloads

# Transcription settings
transcription:
  service: openai  # or "whisper-local"
  model: whisper-1
  language: auto  # auto-detect or specify: en, tr, etc.
  output_dir: ./output/transcripts

# Content processing
processing:
  ai_model: gemini-2.5-flash
  template: default
  output_dir: ./output/markdown

# Knowledge base
knowledge_base:
  base_dir: ./output/knowledge-base
  create_zip: true

# General settings
general:
  log_level: INFO
  progress_bars: true
```

## Project Structure

```
reels-knowledge-base-creator/
├── src/
│   └── reels_scraper/
│       ├── cli/           # Command-line interface
│       ├── scraper/       # Instagram scraping logic
│       ├── downloader/    # Video download module
│       ├── transcription/ # Speech-to-text processing
│       ├── processor/     # Content enhancement & markdown generation
│       └── builder/       # Knowledge base organization
├── tests/                 # Unit and integration tests
├── config/                # Configuration templates
├── output/                # Generated content (gitignored)
│   ├── downloads/         # Downloaded videos
│   ├── transcripts/       # JSON transcripts
│   ├── markdown/          # Generated markdown files
│   └── knowledge-base/    # Final organized knowledge base
└── pyproject.toml
```

## Output Format

Each Reel generates a markdown file with:

```markdown
# Video Title

**Profile**: @username
**Date**: 2024-01-15
**Duration**: 45 seconds
**URL**: https://instagram.com/p/xxxxx

## Executive Summary

AI-generated summary of the main content...

## Full Transcript

[00:00] Introduction to the topic...
[00:15] Key point about...
[00:30] Conclusion...

## Key Takeaways

- Main point 1
- Main point 2
- Main point 3

## Topics

#education #technology #tutorial
```

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## License

MIT License - see LICENSE file for details

## Disclaimer

This tool is for educational purposes. Always respect Instagram's Terms of Service and only scrape publicly available content. Use responsibly and ethically.

## Support

For issues and feature requests, please use the GitHub issue tracker.
