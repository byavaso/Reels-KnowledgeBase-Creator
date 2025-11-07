# Instagram Reels Knowledge Base Creator - Design Document

## Overview

The system is designed as a modular Python CLI application with a pipeline architecture. Each stage (scraping, downloading, transcription, report generation) operates independently, allowing flexible workflows and easy debugging. The architecture prioritizes resilience, caching, and concurrent processing for efficiency. Data flows through stages with JSON as the interchange format, and final outputs are structured markdown files optimized for NotebookLM.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI Interface Layer                          │
│  (Click/Typer) - Command parsing, config loading, progress display  │
└────────────┬────────────────────────────────────────────┬───────────┘
             │                                            │
             ▼                                            ▼
┌────────────────────────┐                  ┌────────────────────────┐
│   Instagram Scraper     │                  │   Configuration        │
│      Component          │                  │      Manager           │
│  - Profile metadata     │                  │  - YAML/ENV parser     │
│  - Reels discovery      │                  │  - Credential store    │
│  - Rate limiting        │                  │  - Validation          │
└──────────┬─────────────┘                  └────────────────────────┘
           │
           ▼
┌────────────────────────┐
│   Video Downloader      │
│  - Concurrent download  │
│  - File validation      │
│  - Resume capability    │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  Transcription Engine   │
│  - Audio extraction     │
│  - Whisper/OpenAI       │
│  - Language detection   │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│   Content Processor     │
│  - AI summarization     │
│  - Topic extraction     │
│  - Markdown generation  │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ Knowledge Base Builder  │
│  - Index generation     │
│  - Catalog creation     │
│  - ZIP packaging        │
└────────────────────────┘
```

### Data Flow

```
Instagram URL
    ↓
[Scraper] → profile_metadata.json, reels_list.json
    ↓
[Downloader] → /downloads/{video_id}.mp4 + download_status.json
    ↓
[Transcriber] → /transcripts/{video_id}.json (raw transcript + metadata)
    ↓
[Processor] → /markdown/{date}_{title}.md (formatted report)
    ↓
[Builder] → /knowledge-base/index.md + organized structure
```

## Components and Interfaces

### 1. Instagram Scraper Component

**Responsibility:** Fetch Instagram profile data and discover all Reels using either instaloader or instagram-private-api.

**Key Classes:**
- `InstagramScraper`: Main scraper orchestrator
- `RateLimiter`: Enforces delays between requests
- `SessionManager`: Handles authentication and session persistence

**Interfaces:**
```python
class InstagramScraper:
    def __init__(self, username: str, credentials: Optional[dict] = None):
        """Initialize scraper with target profile"""
    
    def authenticate(self) -> bool:
        """Login to Instagram with stored credentials"""
    
    def get_profile_info(self) -> ProfileMetadata:
        """Fetch profile metadata (name, bio, follower count)"""
    
    def fetch_reels(self, limit: Optional[int] = None) -> List[ReelMetadata]:
        """Discover and fetch all Reels metadata"""
    
    def save_metadata(self, output_path: Path) -> None:
        """Save scraped data to JSON"""

@dataclass
class ReelMetadata:
    video_id: str
    shortcode: str
    url: str
    caption: str
    timestamp: datetime
    view_count: int
    like_count: int
    comment_count: int
    video_url: str
    duration: int
    thumbnail_url: str
```

**Data Flow:**
- Receives Instagram username/URL from CLI
- Authenticates using session cookies or credentials
- Fetches profile data via Instagram's internal API or web scraping
- Paginate through Reels endpoint to collect all videos
- Outputs structured JSON with metadata

**Performance:**
- Target: Process 100 Reels metadata in < 2 minutes
- Constraints: Instagram rate limit (~1 request/second)

### 2. Video Downloader Component

**Responsibility:** Download Reels videos concurrently with retry logic and validation.

**Key Classes:**
- `VideoDownloader`: Manages download queue and workers
- `DownloadWorker`: Individual download thread/process
- `FileValidator`: Verifies file integrity

**Interfaces:**
```python
class VideoDownloader:
    def __init__(self, max_workers: int = 3, output_dir: Path = Path("downloads")):
        """Initialize downloader with concurrency settings"""
    
    def download_batch(self, reels: List[ReelMetadata]) -> DownloadReport:
        """Download multiple videos concurrently"""
    
    def download_single(self, reel: ReelMetadata, retry_count: int = 3) -> DownloadStatus:
        """Download single video with retry logic"""
    
    def validate_file(self, file_path: Path) -> bool:
        """Check if downloaded file is valid video"""

@dataclass
class DownloadStatus:
    video_id: str
    success: bool
    file_path: Optional[Path]
    file_size: int
    download_time: float
    error_message: Optional[str]
```

**Data Flow:**
- Receives Reels metadata list
- Creates download queue
- Spawns worker threads/processes
- Downloads via yt-dlp or direct HTTP requests
- Validates files using ffprobe
- Updates status JSON

**Performance:**
- Target: 3 concurrent downloads, 2 MB/s per worker
- Constraints: Network bandwidth, Instagram throttling

### 3. Transcription Engine Component

**Responsibility:** Extract audio and generate text transcripts using Whisper or OpenAI API.

**Key Classes:**
- `TranscriptionEngine`: Main transcription orchestrator
- `AudioExtractor`: Extracts audio from video
- `WhisperService`: Local Whisper model interface
- `OpenAIService`: OpenAI API client

**Interfaces:**
```python
class TranscriptionEngine:
    def __init__(self, service: str = "openai", model: str = "whisper-1", language: Optional[str] = None):
        """Initialize with transcription service"""
    
    def transcribe_video(self, video_path: Path) -> Transcript:
        """Extract audio and transcribe"""
    
    def transcribe_batch(self, video_paths: List[Path]) -> List[Transcript]:
        """Batch transcription with concurrency"""
    
    def detect_language(self, audio_path: Path) -> str:
        """Auto-detect spoken language"""

@dataclass
class Transcript:
    video_id: str
    text: str
    language: str
    segments: List[TranscriptSegment]  # with timestamps
    confidence: float
    duration: float

@dataclass
class TranscriptSegment:
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str]
```

**Data Flow:**
- Receives video file path
- Extracts audio using ffmpeg
- Sends to Whisper API or local model
- Processes response with timestamps
- Cleans text (removes fillers, normalizes)
- Saves to JSON

**Performance:**
- Target: 1x realtime (10min video → 10min processing) for local Whisper
- Target: 0.5x realtime (10min video → 5min) for OpenAI API
- GPU acceleration for local processing

### 4. Content Processor Component

**Responsibility:** Transform transcripts into structured markdown reports with AI-generated summaries.

**Key Classes:**
- `ContentProcessor`: Main processing orchestrator
- `AIEnhancer`: GPT-4 integration for summaries
- `MarkdownGenerator`: Template-based report creation
- `TopicExtractor`: NLP-based topic identification

**Interfaces:**
```python
class ContentProcessor:
    def __init__(self, ai_model: str = "gpt-4o-mini", template: str = "default"):
        """Initialize with AI model and template"""
    
    def process_transcript(self, transcript: Transcript, metadata: ReelMetadata) -> MarkdownReport:
        """Generate complete markdown report"""
    
    def generate_summary(self, transcript_text: str, language: str) -> str:
        """AI-generated executive summary"""
    
    def extract_key_points(self, transcript_text: str) -> List[str]:
        """Extract bullet-point takeaways"""
    
    def extract_topics(self, text: str) -> List[str]:
        """Identify main topics/concepts"""

@dataclass
class MarkdownReport:
    video_id: str
    title: str
    content: str  # Full markdown
    summary: str
    topics: List[str]
    key_points: List[str]
    metadata: dict
    file_path: Path
```

**Data Flow:**
- Receives transcript and video metadata
- Calls GPT-4 API for summary generation
- Extracts topics using NER or keyword extraction
- Populates markdown template
- Saves formatted report

**Performance:**
- Target: Process one video in < 30 seconds
- API rate limits: OpenAI tier-based

### 5. Knowledge Base Builder Component

**Responsibility:** Organize all markdown files into a structured knowledge base with indexes.

**Key Classes:**
- `KnowledgeBaseBuilder`: Main builder orchestrator
- `IndexGenerator`: Creates catalog files
- `TopicOrganizer`: Groups content by topic
- `PackageCreator`: Creates ZIP archives

**Interfaces:**
```python
class KnowledgeBaseBuilder:
    def __init__(self, base_dir: Path):
        """Initialize with base directory"""
    
    def build_index(self, reports: List[MarkdownReport]) -> None:
        """Generate master index.md"""
    
    def organize_by_topic(self, reports: List[MarkdownReport]) -> dict:
        """Group reports by topic"""
    
    def generate_statistics(self, reports: List[MarkdownReport]) -> Statistics:
        """Calculate aggregate statistics"""
    
    def create_package(self, output_path: Path) -> None:
        """Create ZIP for NotebookLM import"""

@dataclass
class Statistics:
    total_videos: int
    total_duration: timedelta
    topic_distribution: dict[str, int]
    language_distribution: dict[str, int]
    date_range: tuple[datetime, datetime]
```

**Data Flow:**
- Collects all generated markdown reports
- Scans for topics and metadata
- Generates hierarchical index
- Creates topic-based sub-indexes
- Compiles statistics
- Optionally creates ZIP archive

**Performance:**
- Target: Build index for 1000 videos in < 10 seconds

### 6. CLI Interface & Orchestration

**Responsibility:** Provide user-facing command-line interface and pipeline orchestration.

**Key Classes:**
- `CLI`: Click/Typer command definitions
- `PipelineOrchestrator`: Manages multi-stage execution
- `ConfigManager`: Configuration loading and validation
- `Logger`: Structured logging

**Interfaces:**
```python
# CLI commands using Click
@click.group()
def cli():
    """Instagram Reels Knowledge Base Creator"""

@cli.command()
@click.argument('profile_url')
@click.option('--output-dir', default='./output')
@click.option('--limit', default=None, type=int)
def scrape(profile_url: str, output_dir: str, limit: Optional[int]):
    """Scrape Instagram profile for Reels"""

@cli.command()
@click.option('--input-json', required=True)
@click.option('--workers', default=3)
def download(input_json: str, workers: int):
    """Download videos from metadata"""

@cli.command()
@click.argument('profile_url')
@click.option('--config', type=click.Path())
def full(profile_url: str, config: Optional[str]):
    """Run complete pipeline"""
```

## Data Models

### ProfileMetadata
```python
@dataclass
class ProfileMetadata:
    username: str
    full_name: str
    biography: str
    profile_pic_url: str
    follower_count: int
    following_count: int
    post_count: int
    is_verified: bool
    is_business: bool
    scraped_at: datetime
```

### Pipeline State
```python
@dataclass
class PipelineState:
    profile: ProfileMetadata
    reels_discovered: int
    reels_downloaded: int
    reels_transcribed: int
    reels_processed: int
    started_at: datetime
    completed_at: Optional[datetime]
    errors: List[ErrorLog]
```

## Error Handling

### Network Errors
**Types:** Connection timeout, DNS failure, rate limiting, authentication failure
**Handling:** Exponential backoff retry (3 attempts), fallback to cached data, detailed logging

### API Errors
**Types:** Quota exceeded (OpenAI), invalid response, service unavailable
**Handling:** Graceful degradation (skip AI enhancement if quota exceeded), queue for later retry

### File System Errors
**Types:** Disk full, permission denied, corrupted files
**Handling:** Pre-flight disk space check, proper file locking, validation after writes

### Processing Errors
**Types:** Video codec not supported, audio extraction failure, transcription failure
**Handling:** Skip failed video, log error with context, continue with remaining items

## Testing Strategy

### Unit Tests
- `InstagramScraper`: Mock Instagram API responses
- `VideoDownloader`: Mock file downloads
- `TranscriptionEngine`: Mock Whisper/OpenAI responses
- `MarkdownGenerator`: Template rendering validation
- Coverage target: 80%

### Integration Tests
- End-to-end pipeline with sample data
- Test different video formats
- Test authentication flows
- Test error recovery

### Performance Tests
- Concurrent download stress test (10+ workers)
- Large batch processing (500+ videos)
- Memory usage profiling
- Disk I/O optimization

## Deployment

### Docker Configuration
```yaml
version: '3.8'
services:
  reels-scraper:
    build: .
    volumes:
      - ./output:/app/output
      - ./config:/app/config
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - INSTAGRAM_USERNAME=${INSTAGRAM_USERNAME}
      - INSTAGRAM_PASSWORD=${INSTAGRAM_PASSWORD}
    command: full "target_profile" --config /app/config/config.yaml
```

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-xxx
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

# Optional
TRANSCRIPTION_SERVICE=openai  # or "whisper-local"
AI_MODEL=gpt-4o-mini
MAX_WORKERS=3
OUTPUT_DIR=./output
LOG_LEVEL=INFO
```

### Dependencies
```
Python 3.10+
ffmpeg (for audio extraction)
yt-dlp (for video downloads)
instaloader or instagram-private-api
openai
whisper (optional, for local transcription)
click or typer (CLI)
pydantic (data validation)
jinja2 (markdown templating)
requests
tqdm (progress bars)
```

## Performance Targets

- Profile scraping: < 2 minutes for 100 Reels
- Video download: 2 MB/s per worker
- Transcription: 1x realtime (local) or 0.5x (API)
- Markdown generation: < 30 seconds per video
- Full pipeline: < 2 hours for 100 videos (with transcription)

## Security Considerations

- **Authentication**: Store Instagram credentials in encrypted keyring or environment variables
- **API Keys**: Never commit API keys to version control
- **Rate Limiting**: Respect Instagram's rate limits to avoid IP bans
- **Data Privacy**: Only process publicly available content
- **File Permissions**: Restrict access to downloaded content

## NotebookLM Optimization

### Markdown Format
- Use clear hierarchical headers (H1: Title, H2: Sections)
- Include metadata in YAML frontmatter
- Keep files under 10MB each
- Use descriptive filenames

### Index Structure
- Master index with links to all documents
- Topic-based sub-indexes for navigation
- Include statistics and date ranges
- Add search keywords/tags

### ZIP Packaging
- Organize by topic folders
- Include README.md with import instructions
- Compress with standard ZIP format
- Test import before delivery
