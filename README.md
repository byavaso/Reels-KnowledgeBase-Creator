# Instagram Reels Knowledge Base Creator

A powerful Python CLI tool that transforms Instagram Reels into structured knowledge bases. Perfect for extracting valuable content from educational Instagram accounts and organizing it for AI tools like NotebookLM.

## ✨ Features

- 🎥 **Instagram Scraping**: Automatically discover and collect all Reels from any public Instagram profile
- ⬇️ **Video Download**: Concurrent downloading with retry logic and automatic resume capability
- 🎤 **Transcription**: Convert speech to text using OpenAI Whisper API or local Whisper models
- 🤖 **AI Enhancement**: Generate summaries and extract key topics using Google Gemini
- 📝 **Markdown Generation**: Create structured, NotebookLM-ready documentation
- 📚 **Knowledge Base**: Organize content by topics with master index and statistics
- 🔄 **Resume Capability**: Automatically resume interrupted operations without reprocessing
- 📦 **ZIP Export**: Create ready-to-upload archives for NotebookLM
- ⚡ **Progress Tracking**: Real-time progress with persistent state across all stages

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
reels-scraper full profile_name

# With limit
reels-scraper full profile_name --limit 10

# The pipeline will automatically:
# 1. Scrape Instagram profile for Reels metadata
# 2. Download videos concurrently
# 3. Transcribe videos using Whisper
# 4. Generate AI-enhanced markdown reports
# 5. Build organized knowledge base with index
# 6. (Optional) Create ZIP archive for NotebookLM

# If interrupted, simply run the same command again!
# The tool will automatically resume from where it left off.
```

### 3. Use Individual Commands

```bash
# Step 1: Scrape Instagram profile
reels-scraper scrape profile_name --limit 50

# Step 2: Download videos
reels-scraper download --input-json ./output/reels_list.json

# Step 3: Transcribe videos
reels-scraper transcribe --video-dir ./output/downloads

# Step 4: Generate markdown reports
reels-scraper generate --transcript-dir ./output/transcripts

# Step 5: Build knowledge base with topic organization
reels-scraper index --markdown-dir ./output/markdown --create-zip
```

### 4. Resume Interrupted Operations

```bash
# If any command is interrupted (network issue, crash, etc.),
# simply run it again - it will automatically resume!

# Example: Download was interrupted at 15/50 videos
reels-scraper download --input-json ./output/reels_list.json
# Output: "Resuming download: 15 already completed, 35 remaining"

# Works for all batch operations:
# - Video downloads
# - Transcriptions
# - Content processing
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

# Concurrent transcription (API rate limits apply)
reels-scraper transcribe --video-dir ./output/downloads --workers 2

# Using local Whisper (offline, free)
# Configure in config.yaml: transcription.service = "whisper-local"
```

### Generate Command

```bash
# Generate markdown from transcripts
reels-scraper generate --transcript-dir ./output/transcripts

# With reel metadata for enhanced reports
reels-scraper generate --transcript-dir ./output/transcripts \
  --reels-json ./output/reels_list.json
```

### Index Command (NEW)

```bash
# Build organized knowledge base from markdown files
reels-scraper index --markdown-dir ./output/markdown

# Organize by topics (default)
reels-scraper index --markdown-dir ./output/markdown --organize-by-topic

# Create flat structure
reels-scraper index --markdown-dir ./output/markdown --flat

# Create ZIP archive for NotebookLM
reels-scraper index --markdown-dir ./output/markdown --create-zip

# Custom ZIP name
reels-scraper index --markdown-dir ./output/markdown \
  --create-zip --zip-name my-knowledge-base.zip
```

## Configuration

Create a `config.yaml` file for persistent settings:

```yaml
# Instagram settings
instagram:
  username: null  # Optional: for private profiles or rate limit mitigation
  password: null  # Optional: for private profiles
  rate_limit_delay: 2.0  # Seconds between requests (increase if hitting limits)
  session_file: session.json  # Session persistence

# Download settings
download:
  max_workers: 3  # Concurrent downloads (1-10)
  retry_count: 3  # Retry attempts per video
  retry_delay: 5.0  # Initial retry delay (exponential backoff)
  output_dir: ./output/downloads
  skip_existing: true  # Skip already downloaded videos

# Transcription settings
transcription:
  service: openai  # "openai" or "whisper-local"
  model: whisper-1  # For OpenAI, or "base"/"small"/"medium" for local
  language: auto  # Auto-detect or specify: en, tr, es, etc.
  output_dir: ./output/transcripts
  max_workers: 2  # Concurrent transcriptions (respect API limits)

# Content processing
processing:
  ai_service: gemini  # AI service for enhancement
  ai_model: gemini-2.0-flash-exp  # Gemini model
  template: default  # Markdown template name
  output_dir: ./output/markdown
  extract_topics: true  # Extract topic tags
  generate_summary: true  # Generate AI summaries
  max_summary_length: 500  # Max words in summary

# Knowledge base organization
knowledge_base:
  base_dir: ./output/knowledge-base
  create_index: true  # Generate master index.md
  organize_by_topic: true  # Organize files by extracted topics
  create_zip: false  # Auto-create ZIP archive
  zip_name: knowledge-base.zip  # ZIP file name

# General settings
general:
  log_level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_file: ./output/reels_scraper.log
  progress_bars: true  # Show progress bars
  verbose: false  # Verbose output
```

## Project Structure

```
reels-knowledge-base-creator/
├── src/
│   └── reels_scraper/
│       ├── cli/              # Command-line interface
│       ├── scraper/          # Instagram scraping logic
│       │   ├── scraper.py    # Main scraper
│       │   ├── rate_limiter.py  # Rate limiting
│       │   └── session_manager.py  # Authentication
│       ├── downloader/       # Video download module
│       │   └── downloader.py # Concurrent downloader with resume
│       ├── transcription/    # Speech-to-text processing
│       │   ├── whisper_service.py  # OpenAI Whisper API
│       │   ├── local_whisper.py    # Local Whisper support
│       │   └── engine.py     # Transcription orchestration
│       ├── processor/        # Content enhancement & markdown
│       │   ├── ai_enhancer.py      # Gemini AI integration
│       │   ├── markdown_generator.py
│       │   └── processor.py  # Batch processing
│       ├── builder/          # Knowledge base organization
│       │   └── builder.py    # Topic organization & indexing
│       ├── progress.py       # Progress tracking & resume
│       ├── config.py         # Configuration management
│       ├── models.py         # Data models (Pydantic)
│       └── logger.py         # Logging setup
├── tests/                    # Unit and integration tests
├── output/                   # Generated content (gitignored)
│   ├── downloads/            # Downloaded videos
│   │   └── .download_progress.json  # Download progress
│   ├── transcripts/          # JSON transcripts
│   │   └── .transcription_progress.json
│   ├── markdown/             # Generated markdown files
│   │   └── .processing_progress.json
│   └── knowledge-base/       # Final organized knowledge base
│       ├── index.md          # Master index
│       ├── stats.json        # Statistics
│       ├── topic1/           # Topic-based organization
│       ├── topic2/
│       └── ...
├── config.example.yaml       # Configuration template
├── .env.example              # Environment variables template
└── pyproject.toml            # Package metadata
```

## Output Format

### Markdown Files

Each Reel generates a markdown file with:

```markdown
# Video Title

**Profile**: @username
**Date**: 2024-01-15
**Duration**: 45 seconds
**URL**: https://instagram.com/p/xxxxx
**Views**: 12.5K
**Likes**: 856

---

## Executive Summary

AI-generated summary of the main content...

---

## Full Transcript

[00:00] Introduction to the topic...
[00:15] Key point about...
[00:30] Conclusion...

---

## Key Takeaways

- Main point 1
- Main point 2
- Main point 3

---

## Topics

#education #technology #tutorial

---

**Language**: English
**Word Count**: 186
**Transcription Service**: openai-whisper-1
**Generated**: 2024-01-15 14:30:00
```

### Knowledge Base Structure

When organized by topics:

```
knowledge-base/
├── index.md                    # Master index with statistics
├── stats.json                  # Detailed statistics
├── education/                  # Topic: Education
│   ├── video1.md
│   ├── video2.md
│   └── ...
├── technology/                 # Topic: Technology
│   ├── video3.md
│   └── ...
├── tutorial/                   # Topic: Tutorial
│   └── ...
└── uncategorized/             # Videos without clear topics
    └── ...
```

### Progress Files (Auto-generated)

Progress files enable resume capability:

- `.download_progress.json` - Tracks download status per video
- `.transcription_progress.json` - Tracks transcription status
- `.processing_progress.json` - Tracks AI processing status

These files are automatically created and updated during batch operations.

## Advanced Features

### Local Whisper Support

Use local Whisper models for offline transcription (no API costs):

```yaml
# config.yaml
transcription:
  service: whisper-local
  model: base  # tiny, base, small, medium, large
  language: auto
```

**Benefits:**
- 🆓 Free (no API costs)
- 🔒 Private (data stays local)
- ⚡ Fast (with GPU)

**Requirements:**
- Install: `pip install openai-whisper`
- For GPU: CUDA-compatible GPU + PyTorch with CUDA

### Resume Capability

All batch operations support automatic resumption:

**How it works:**
1. Progress is saved after each item completes
2. If interrupted, run the same command again
3. Tool automatically skips completed items
4. Only processes remaining/failed items

**Example:**
```bash
# First run (interrupted at 30/100)
reels-scraper full profile_name

# Second run (resumes from item 31)
reels-scraper full profile_name
# Output: "Resuming download: 30 already completed, 70 remaining"
```

**Progress files:**
- Located in output directories with `.` prefix
- JSON format with item-level status
- Safe to delete to restart from scratch

### Rate Limiting & Instagram Access

**Best practices for Instagram scraping:**

1. **Use authentication** for better rate limits:
   ```yaml
   instagram:
     username: your_username
     password: your_password
   ```

2. **Increase delays** if hitting limits:
   ```yaml
   instagram:
     rate_limit_delay: 3.0  # Default: 2.0
   ```

3. **Scrape in batches** with limits:
   ```bash
   reels-scraper scrape profile_name --limit 50
   ```

4. **Session persistence** - Sessions are automatically saved and reused

### Bulk Processing Tips

**For large profiles (100+ Reels):**

```bash
# 1. Scrape with limit
reels-scraper scrape profile_name --limit 100

# 2. Download with resume enabled (default)
reels-scraper download --input-json ./output/reels_list.json

# 3. Transcribe in smaller batches
reels-scraper transcribe --video-dir ./output/downloads --workers 2

# 4. Process with resume
reels-scraper generate --transcript-dir ./output/transcripts

# 5. Build knowledge base
reels-scraper index --markdown-dir ./output/markdown --create-zip
```

**Benefits:**
- 💰 Save API costs (resume from failures)
- ⏱️ Better time management (run in sessions)
- 🛡️ Avoid rate limits (respect Instagram's limits)

## Troubleshooting

### Common Issues

**1. Instagram Rate Limiting**
```
Error: Too many requests
Solution: Increase rate_limit_delay in config, use authentication
```

**2. FFmpeg Not Found**
```
Error: ffmpeg not found
Solution: Install ffmpeg (macOS: brew install ffmpeg, Ubuntu: apt install ffmpeg)
```

**3. API Key Errors**
```
Error: Invalid API key
Solution: Check .env file, ensure keys are valid and active
```

**4. Memory Issues (Large Videos)**
```
Error: Out of memory
Solution: Reduce max_workers in config, process in smaller batches
```

**5. Resume Not Working**
```
Issue: Progress not resuming
Solution: Check for .progress.json files in output directories, ensure enable_resume=true
```

### Debug Mode

Enable verbose logging:

```bash
# CLI flag
reels-scraper full profile_name --verbose

# Config file
general:
  log_level: DEBUG
  verbose: true
```

## Performance Optimization

### Concurrent Processing

Balance speed vs. resource usage:

```yaml
download:
  max_workers: 5  # More workers = faster downloads

transcription:
  max_workers: 2  # Limited by API rate limits

# Processing is sequential (Gemini rate limits)
```

### Local Whisper Performance

**GPU Acceleration:**
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Use larger models with GPU
transcription:
  service: whisper-local
  model: medium  # or large with powerful GPU
```

**Model Size vs. Accuracy:**
- `tiny`: Fastest, lowest accuracy (~1GB RAM)
- `base`: Good balance (~1GB RAM)
- `small`: Better accuracy (~2GB RAM)
- `medium`: High accuracy (~5GB RAM)
- `large`: Best accuracy (~10GB RAM)

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## License

MIT License - see LICENSE file for details

## Disclaimer

This tool is for educational purposes. Always respect Instagram's Terms of Service and only scrape publicly available content. Use responsibly and ethically.

## Support

For issues and feature requests, please use the GitHub issue tracker.
