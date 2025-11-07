"""Configuration management for Instagram Reels Knowledge Base Creator."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class InstagramConfig(BaseSettings):
    """Instagram-specific configuration."""

    username: Optional[str] = Field(default=None, description="Instagram username")
    password: Optional[str] = Field(default=None, description="Instagram password")
    rate_limit_delay: float = Field(
        default=2.0, ge=0.1, description="Delay between requests in seconds"
    )
    session_file: str = Field(default="session.json", description="Session file path")

    model_config = SettingsConfigDict(env_prefix="INSTAGRAM_")


class DownloadConfig(BaseSettings):
    """Download-specific configuration."""

    max_workers: int = Field(default=3, ge=1, le=10, description="Number of concurrent workers")
    retry_count: int = Field(default=3, ge=0, le=10, description="Number of retry attempts")
    retry_delay: float = Field(default=5.0, ge=0.1, description="Initial retry delay in seconds")
    output_dir: Path = Field(default=Path("./output/downloads"), description="Download directory")
    skip_existing: bool = Field(default=True, description="Skip already downloaded videos")
    video_quality: str = Field(default="best", description="Video quality preference")

    @field_validator("output_dir", mode="before")
    @classmethod
    def validate_output_dir(cls, v: str | Path) -> Path:
        """Convert string to Path and create directory if needed."""
        path = Path(v) if isinstance(v, str) else v
        return path

    model_config = SettingsConfigDict(env_prefix="DOWNLOAD_")


class TranscriptionConfig(BaseSettings):
    """Transcription-specific configuration."""

    service: str = Field(
        default="openai", description="Transcription service: openai or whisper-local"
    )
    model: str = Field(default="whisper-1", description="Model to use for transcription")
    language: str = Field(default="auto", description="Language code or 'auto' for detection")
    output_dir: Path = Field(
        default=Path("./output/transcripts"), description="Transcript directory"
    )
    include_timestamps: bool = Field(default=True, description="Include timestamps in transcripts")
    max_workers: int = Field(
        default=2, ge=1, le=5, description="Number of concurrent transcription workers"
    )

    @field_validator("service")
    @classmethod
    def validate_service(cls, v: str) -> str:
        """Validate transcription service."""
        if v not in ["openai", "whisper-local"]:
            raise ValueError("service must be 'openai' or 'whisper-local'")
        return v

    @field_validator("output_dir", mode="before")
    @classmethod
    def validate_output_dir(cls, v: str | Path) -> Path:
        """Convert string to Path."""
        return Path(v) if isinstance(v, str) else v

    model_config = SettingsConfigDict(env_prefix="TRANSCRIPTION_")


class ProcessingConfig(BaseSettings):
    """Content processing configuration."""

    ai_service: str = Field(default="gemini", description="AI service: gemini or openai")
    ai_model: str = Field(
        default="gemini-2.0-flash-exp", description="AI model for summarization"
    )
    template: str = Field(default="default", description="Template name to use")
    output_dir: Path = Field(default=Path("./output/markdown"), description="Markdown directory")
    extract_topics: bool = Field(default=True, description="Extract topics from content")
    generate_summary: bool = Field(default=True, description="Generate AI summary")
    max_summary_length: int = Field(
        default=500, ge=50, le=2000, description="Maximum summary length in words"
    )

    @field_validator("ai_service")
    @classmethod
    def validate_ai_service(cls, v: str) -> str:
        """Validate AI service."""
        if v not in ["gemini", "openai"]:
            raise ValueError("ai_service must be 'gemini' or 'openai'")
        return v

    @field_validator("output_dir", mode="before")
    @classmethod
    def validate_output_dir(cls, v: str | Path) -> Path:
        """Convert string to Path."""
        return Path(v) if isinstance(v, str) else v

    model_config = SettingsConfigDict(env_prefix="PROCESSING_")


class KnowledgeBaseConfig(BaseSettings):
    """Knowledge base configuration."""

    base_dir: Path = Field(
        default=Path("./output/knowledge-base"), description="Knowledge base directory"
    )
    create_index: bool = Field(default=True, description="Create master index.md")
    organize_by_topic: bool = Field(default=True, description="Organize files by topics")
    create_zip: bool = Field(default=False, description="Create ZIP archive")
    zip_name: str = Field(default="knowledge-base.zip", description="ZIP archive name")

    @field_validator("base_dir", mode="before")
    @classmethod
    def validate_base_dir(cls, v: str | Path) -> Path:
        """Convert string to Path."""
        return Path(v) if isinstance(v, str) else v

    model_config = SettingsConfigDict(env_prefix="KNOWLEDGE_BASE_")


class GeneralConfig(BaseSettings):
    """General application configuration."""

    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[Path] = Field(
        default=Path("./output/reels_scraper.log"), description="Log file path"
    )
    progress_bars: bool = Field(default=True, description="Show progress bars")
    verbose: bool = Field(default=False, description="Verbose output")
    dry_run: bool = Field(default=False, description="Dry run mode")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("log_file", mode="before")
    @classmethod
    def validate_log_file(cls, v: str | Path | None) -> Optional[Path]:
        """Convert string to Path."""
        if v is None:
            return None
        return Path(v) if isinstance(v, str) else v

    model_config = SettingsConfigDict(env_prefix="GENERAL_")


class Config(BaseSettings):
    """Main configuration class combining all settings."""

    instagram: InstagramConfig = Field(default_factory=InstagramConfig)
    download: DownloadConfig = Field(default_factory=DownloadConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    knowledge_base: KnowledgeBaseConfig = Field(default_factory=KnowledgeBaseConfig)
    general: GeneralConfig = Field(default_factory=GeneralConfig)

    # API Keys (from environment only)
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    google_api_key: Optional[str] = Field(default=None, description="Google API key")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def load_from_yaml(cls, yaml_path: Path | str) -> "Config":
        """Load configuration from YAML file and merge with environment variables.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            Config instance with merged settings

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValueError: If YAML is invalid
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")

        # Create nested config objects
        config_data = {}

        # Process each section
        if "instagram" in yaml_data:
            config_data["instagram"] = InstagramConfig(**yaml_data["instagram"])
        if "download" in yaml_data:
            config_data["download"] = DownloadConfig(**yaml_data["download"])
        if "transcription" in yaml_data:
            config_data["transcription"] = TranscriptionConfig(**yaml_data["transcription"])
        if "processing" in yaml_data:
            config_data["processing"] = ProcessingConfig(**yaml_data["processing"])
        if "knowledge_base" in yaml_data:
            config_data["knowledge_base"] = KnowledgeBaseConfig(**yaml_data["knowledge_base"])
        if "general" in yaml_data:
            config_data["general"] = GeneralConfig(**yaml_data["general"])

        # Create main config (environment variables will override)
        return cls(**config_data)

    @classmethod
    def load(cls, config_path: Optional[Path | str] = None) -> "Config":
        """Load configuration from file and environment.

        Args:
            config_path: Optional path to YAML config file

        Returns:
            Config instance
        """
        if config_path:
            return cls.load_from_yaml(config_path)

        # Try to find config.yaml in current directory
        default_paths = [Path("config.yaml"), Path("config.yml")]
        for path in default_paths:
            if path.exists():
                return cls.load_from_yaml(path)

        # No config file found, use defaults + environment
        return cls()

    def create_output_directories(self) -> None:
        """Create all configured output directories."""
        directories = [
            self.download.output_dir,
            self.transcription.output_dir,
            self.processing.output_dir,
            self.knowledge_base.base_dir,
        ]

        if self.general.log_file:
            directories.append(self.general.log_file.parent)

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def validate_api_keys(self, require_openai: bool = True, require_google: bool = False) -> None:
        """Validate that required API keys are set.

        Args:
            require_openai: Whether OpenAI API key is required
            require_google: Whether Google API key is required

        Raises:
            ValueError: If required API keys are missing
        """
        errors = []

        if require_openai and not self.openai_api_key:
            errors.append("OPENAI_API_KEY environment variable is required")

        if require_google and not self.google_api_key:
            errors.append("GOOGLE_API_KEY environment variable is required")

        if errors:
            raise ValueError("\n".join(errors))


# Global config instance (initialized lazily)
_config: Optional[Config] = None


def get_config(config_path: Optional[Path | str] = None, reload: bool = False) -> Config:
    """Get or create global configuration instance.

    Args:
        config_path: Optional path to config file
        reload: Force reload of configuration

    Returns:
        Config instance
    """
    global _config

    if _config is None or reload:
        _config = Config.load(config_path)

    return _config
