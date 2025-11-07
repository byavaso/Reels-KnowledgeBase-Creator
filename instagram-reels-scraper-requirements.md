# Instagram Reels Knowledge Base Creator - Requirements Document

## Introduction

Instagram Reels Knowledge Base Creator, Instagram sayfalarından video içeriklerini toplayıp transcript'lerini çıkartan ve NotebookLM gibi AI araçlarında kullanılmak üzere yapılandırılmış markdown dokümanları oluşturan bir CLI aracıdır. Eğitici içerik üreten Instagram sayfalarındaki geçmiş bilgileri sistematik bir knowledge base'e dönüştürmek için tasarlanmıştır.

## Glossary

- **Reels**: Instagram'ın kısa video formatı
- **Transcript**: Video içindeki konuşmanın yazıya dökülmüş hali
- **Scraping**: Web/platform verilerinin otomatik olarak toplanması
- **Knowledge Base**: Yapılandırılmış bilgi deposu
- **NotebookLM**: Google'ın doküman tabanlı AI asistan aracı
- **Metadata**: Video hakkındaki bilgiler (tarih, başlık, görüntülenme sayısı vb.)
- **Rate Limiting**: API/scraping hız sınırlaması
- **Batch Processing**: Toplu işleme

## Requirements

### REQ-1: Instagram Profil Scraping

**User Story:** As a user, I want to provide an Instagram profile URL and scrape all its Reels, so that I can collect educational video content for later processing.

#### Acceptance Criteria

1. THE system SHALL accept an Instagram profile URL or username as input
2. THE system SHALL authenticate with Instagram (using session cookies or API credentials)
3. THE system SHALL discover and list all Reels from the target profile
4. THE system SHALL extract video metadata (URL, title, caption, date, views, likes)
5. THE system SHALL handle paginated results to fetch all historical Reels
6. THE system SHALL respect Instagram rate limits with configurable delays between requests
7. THE system SHALL save raw video metadata to a JSON file for reference
8. IF authentication fails, THEN THE system SHALL provide clear error messages
9. THE system SHALL support resume functionality for interrupted scraping sessions

### REQ-2: Video Download

**User Story:** As a user, I want videos to be downloaded locally, so that transcripts can be extracted even if videos are deleted from Instagram.

#### Acceptance Criteria

1. THE system SHALL download Reels videos in the highest available quality
2. THE system SHALL save videos with unique identifiers (video ID or timestamp)
3. THE system SHALL skip already downloaded videos to avoid duplicates
4. THE system SHALL organize videos in a structured folder hierarchy (e.g., `/downloads/{profile_name}/{video_id}.mp4`)
5. THE system SHALL validate downloaded files for corruption
6. THE system SHALL support bandwidth throttling to avoid network congestion
7. IF a download fails, THEN THE system SHALL retry up to 3 times with exponential backoff
8. THE system SHALL log all download activities with timestamps

### REQ-3: Transcript Extraction

**User Story:** As a user, I want automatic speech-to-text transcription of videos, so that I can extract textual knowledge from video content.

#### Acceptance Criteria

1. THE system SHALL extract audio from downloaded video files
2. THE system SHALL use a speech-to-text service (Whisper API, OpenAI API, or local Whisper model)
3. THE system SHALL detect and set the correct language for transcription (Turkish/English auto-detection)
4. THE system SHALL include timestamps in transcripts for reference
5. THE system SHALL handle multiple speakers if detectable
6. THE system SHALL clean transcripts by removing filler words and repetitions
7. THE system SHALL store raw transcripts in JSON format with metadata
8. IF transcription fails, THEN THE system SHALL log the error and continue with next video
9. THE system SHALL support both cloud-based and local transcription options
10. THE transcription process SHALL complete within 5 minutes per 10-minute video

### REQ-4: Content Structuring & Markdown Report Generation

**User Story:** As a user, I want transcripts converted into structured markdown documents, so that I can use them as knowledge base entries in NotebookLM.

#### Acceptance Criteria

1. THE system SHALL generate one markdown file per video
2. THE markdown document SHALL include a structured header with:
   - Video title
   - Publication date
   - Instagram URL
   - Video duration
   - Author/channel name
   - Tags/topics (if extractable)
3. THE system SHALL organize transcript content with:
   - Executive summary (AI-generated)
   - Main content sections with timestamps
   - Key takeaways (bullet points)
   - Referenced concepts/entities
4. THE system SHALL use AI (GPT-4 or similar) to generate summaries and extract key points
5. THE markdown SHALL follow a consistent template for all videos
6. THE system SHALL save markdown files with descriptive names (e.g., `{date}_{video-title}.md`)
7. THE system SHALL create an index/catalog markdown file listing all processed videos
8. THE system SHALL support custom templates for different content types
9. THE generated markdown SHALL be compatible with NotebookLM's import requirements

### REQ-5: Knowledge Base Organization

**User Story:** As a user, I want all processed content organized in a knowledge base structure, so that I can easily import it into NotebookLM and search through it.

#### Acceptance Criteria

1. THE system SHALL create a master directory structure:
   - `/knowledge-base/{profile_name}/`
   - `/knowledge-base/{profile_name}/markdown/`
   - `/knowledge-base/{profile_name}/metadata/`
   - `/knowledge-base/{profile_name}/index.md`
2. THE system SHALL generate a comprehensive index.md with:
   - Total video count
   - Processing date
   - List of all videos with links to their markdown files
   - Topic/category breakdown
3. THE system SHALL support topic-based categorization (AI-detected or manual tags)
4. THE system SHALL create topic-specific sub-indexes
5. THE system SHALL generate a statistics report (total videos, total duration, common topics)
6. THE system SHALL support merging multiple scraping sessions

### REQ-6: Configuration & CLI Interface

**User Story:** As a user, I want a simple CLI with configuration options, so that I can customize the scraping and processing workflow.

#### Acceptance Criteria

1. THE system SHALL provide a command-line interface with subcommands:
   - `scrape`: Fetch Instagram profile data
   - `download`: Download videos
   - `transcribe`: Generate transcripts
   - `generate`: Create markdown reports
   - `index`: Build knowledge base index
   - `full`: Run complete pipeline
2. THE system SHALL support configuration via:
   - Command-line arguments
   - Config file (YAML/JSON)
   - Environment variables
3. THE system SHALL provide configurable options:
   - Instagram credentials
   - Transcription service selection (Whisper/OpenAI)
   - AI model for summarization (GPT-4/GPT-3.5)
   - Language preferences
   - Rate limiting settings
   - Output directory paths
4. THE system SHALL display progress bars for long-running operations
5. THE system SHALL provide verbose/debug logging modes
6. THE system SHALL support dry-run mode to preview actions without executing

### REQ-7: Error Handling & Resilience

**User Story:** As a user, I want the system to handle errors gracefully, so that one failure doesn't stop the entire processing pipeline.

#### Acceptance Criteria

1. THE system SHALL continue processing remaining videos if one video fails
2. THE system SHALL log all errors with context (video ID, error message, timestamp)
3. THE system SHALL generate an error report at the end of processing
4. THE system SHALL support resume/retry for failed operations
5. THE system SHALL validate inputs before processing
6. IF Instagram blocks access, THEN THE system SHALL detect it and suggest solutions
7. THE system SHALL handle network timeouts with automatic retry

### REQ-8: Performance & Efficiency

**User Story:** As a user, I want the system to process videos efficiently, so that I can scrape large profiles without excessive wait times.

#### Acceptance Criteria

1. THE system SHALL support concurrent downloads (configurable worker count)
2. THE system SHALL support concurrent transcription processing
3. THE system SHALL cache intermediate results to avoid reprocessing
4. THE system SHALL skip already processed videos
5. THE download process SHALL achieve at least 2 MB/s throughput per worker
6. THE transcription SHALL utilize GPU if available for local Whisper models
7. THE system SHALL provide estimated time remaining for long operations

### REQ-9: NotebookLM Compatibility

**User Story:** As a user, I want output optimized for NotebookLM, so that I can directly import the knowledge base without manual formatting.

#### Acceptance Criteria

1. THE markdown files SHALL follow NotebookLM's preferred format
2. THE system SHALL limit file sizes to NotebookLM's constraints (if any)
3. THE system SHALL include proper metadata headers for NotebookLM indexing
4. THE system SHALL test export compatibility with NotebookLM
5. THE system SHALL provide a zip archive option for batch import
6. THE documentation SHALL include NotebookLM import instructions

### REQ-10: Data Privacy & Legal Compliance

**User Story:** As a user, I want the system to respect privacy and legal boundaries, so that I only process publicly available content appropriately.

#### Acceptance Criteria

1. THE system SHALL only access publicly available profiles
2. THE system SHALL include disclaimers about Instagram Terms of Service
3. THE system SHALL not store Instagram credentials in plain text
4. THE system SHALL provide options to exclude certain content types
5. THE documentation SHALL include usage guidelines and legal considerations
6. THE system SHALL respect robots.txt and rate limiting policies
