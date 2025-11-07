"""Instagram Reels scraper."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import instaloader
from instaloader import Profile

from ..logger import get_logger
from ..models import ProfileMetadata, ReelMetadata
from .rate_limiter import RateLimiter
from .session_manager import SessionManager

logger = get_logger(__name__)


class InstagramScraper:
    """Scraper for Instagram profiles and Reels."""

    def __init__(
        self,
        username: str,
        instagram_username: Optional[str] = None,
        instagram_password: Optional[str] = None,
        rate_limit_delay: float = 2.0,
        session_file: Path = Path("session.json"),
    ):
        """Initialize Instagram scraper.

        Args:
            username: Target Instagram profile username to scrape
            instagram_username: Optional credentials for authentication
            instagram_password: Optional credentials for authentication
            rate_limit_delay: Delay between requests in seconds
            session_file: Path to session file
        """
        self.target_username = username
        self.session_manager = SessionManager(session_file)
        self.rate_limiter = RateLimiter(delay=rate_limit_delay)
        self.profile: Optional[Profile] = None

        logger.info(f"Instagram scraper initialized for profile: {username}")

        # Authenticate
        if not self.session_manager.authenticate(instagram_username, instagram_password):
            logger.warning("Authentication failed, continuing with limited access")

    def _extract_profile_metadata(self, profile: Profile) -> ProfileMetadata:
        """Extract metadata from Instagram profile.

        Args:
            profile: Instaloader Profile object

        Returns:
            ProfileMetadata instance
        """
        return ProfileMetadata(
            username=profile.username,
            full_name=profile.full_name or "",
            biography=profile.biography or "",
            profile_pic_url=profile.profile_pic_url,
            follower_count=profile.followers,
            following_count=profile.followees,
            post_count=profile.mediacount,
            is_verified=profile.is_verified,
            is_business=profile.is_business_account,
            scraped_at=datetime.now(),
        )

    def _extract_reel_metadata(self, post: instaloader.Post) -> Optional[ReelMetadata]:
        """Extract metadata from an Instagram Reel.

        Args:
            post: Instaloader Post object

        Returns:
            ReelMetadata instance if post is a Reel, None otherwise
        """
        # Check if post is a video (Reel)
        if not post.is_video:
            return None

        try:
            return ReelMetadata(
                video_id=str(post.mediaid),
                shortcode=post.shortcode,
                url=f"https://www.instagram.com/p/{post.shortcode}/",
                caption=post.caption or "" if post.caption else "",
                timestamp=post.date_utc,
                view_count=post.video_view_count if post.video_view_count else 0,
                like_count=post.likes,
                comment_count=post.comments,
                video_url=post.video_url if post.video_url else "",
                duration=post.video_duration if post.video_duration else 0.0,
                thumbnail_url=post.url,
                owner_username=post.owner_username,
            )
        except Exception as e:
            logger.error(f"Failed to extract metadata from post {post.shortcode}: {e}")
            return None

    def get_profile_info(self) -> ProfileMetadata:
        """Fetch Instagram profile information.

        Returns:
            ProfileMetadata instance

        Raises:
            ValueError: If profile not found
        """
        try:
            loader = self.session_manager.get_loader()

            logger.info(f"Fetching profile info for: {self.target_username}")

            with self.rate_limiter:
                self.profile = Profile.from_username(loader.context, self.target_username)

            metadata = self._extract_profile_metadata(self.profile)

            logger.info(
                f"Profile found: {metadata.full_name} (@{metadata.username}) - "
                f"{metadata.follower_count} followers, {metadata.post_count} posts"
            )

            return metadata

        except instaloader.exceptions.ProfileNotExistsException:
            raise ValueError(f"Profile not found: {self.target_username}")
        except Exception as e:
            logger.error(f"Failed to fetch profile info: {e}")
            raise

    def fetch_reels(self, limit: Optional[int] = None) -> List[ReelMetadata]:
        """Fetch all Reels from the target profile.

        Args:
            limit: Maximum number of Reels to fetch (None for all)

        Returns:
            List of ReelMetadata instances
        """
        try:
            if not self.profile:
                logger.info("Profile not loaded, fetching profile info first")
                self.get_profile_info()

            logger.info(
                f"Starting to fetch Reels from {self.target_username}"
                + (f" (limit: {limit})" if limit else " (no limit)")
            )

            reels: List[ReelMetadata] = []
            processed_count = 0
            reel_count = 0

            # Iterate through all posts
            for post in self.profile.get_posts():
                with self.rate_limiter:
                    processed_count += 1

                    # Extract metadata if it's a video/Reel
                    reel_metadata = self._extract_reel_metadata(post)

                    if reel_metadata:
                        reels.append(reel_metadata)
                        reel_count += 1

                        logger.debug(
                            f"Found Reel {reel_count}: {reel_metadata.shortcode} "
                            f"({reel_metadata.duration:.1f}s, {reel_metadata.view_count} views)"
                        )

                        # Check limit
                        if limit and reel_count >= limit:
                            logger.info(f"Reached limit of {limit} Reels")
                            break

                    # Log progress every 10 posts
                    if processed_count % 10 == 0:
                        logger.info(
                            f"Processed {processed_count} posts, found {reel_count} Reels"
                        )

            logger.info(
                f"Scraping complete: Found {reel_count} Reels out of {processed_count} posts"
            )

            return reels

        except Exception as e:
            logger.error(f"Failed to fetch Reels: {e}")
            raise

    def save_metadata(
        self,
        profile_metadata: ProfileMetadata,
        reels: List[ReelMetadata],
        output_dir: Path,
    ) -> None:
        """Save scraped metadata to JSON files.

        Args:
            profile_metadata: Profile metadata to save
            reels: List of Reel metadata to save
            output_dir: Output directory for JSON files
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save profile metadata
            profile_file = output_dir / "profile_metadata.json"
            with open(profile_file, "w", encoding="utf-8") as f:
                json.dump(profile_metadata.model_dump(), f, indent=2, default=str)
            logger.info(f"Saved profile metadata to {profile_file}")

            # Save Reels list
            reels_file = output_dir / "reels_list.json"
            reels_data = [reel.model_dump() for reel in reels]
            with open(reels_file, "w", encoding="utf-8") as f:
                json.dump(reels_data, f, indent=2, default=str)
            logger.info(f"Saved {len(reels)} Reels metadata to {reels_file}")

            # Save summary
            summary_file = output_dir / "scraping_summary.json"
            summary = {
                "profile": profile_metadata.username,
                "total_reels": len(reels),
                "scraped_at": datetime.now().isoformat(),
                "reels_file": str(reels_file),
                "profile_file": str(profile_file),
            }
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Saved scraping summary to {summary_file}")

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise

    def scrape_profile(
        self, limit: Optional[int] = None, output_dir: Path = Path("./output")
    ) -> tuple[ProfileMetadata, List[ReelMetadata]]:
        """Complete profile scraping workflow.

        Args:
            limit: Maximum number of Reels to fetch
            output_dir: Output directory for metadata

        Returns:
            Tuple of (ProfileMetadata, List[ReelMetadata])
        """
        logger.info(f"Starting complete scraping workflow for {self.target_username}")

        # Fetch profile info
        profile_metadata = self.get_profile_info()

        # Fetch Reels
        reels = self.fetch_reels(limit=limit)

        # Save metadata
        self.save_metadata(profile_metadata, reels, output_dir)

        logger.info(
            f"Scraping workflow complete: {len(reels)} Reels from @{profile_metadata.username}"
        )

        return profile_metadata, reels
