"""Instagram session management."""

import json
from pathlib import Path
from typing import Optional

import instaloader

from ..logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manage Instagram session and authentication."""

    def __init__(self, session_file: Path = Path("session.json")):
        """Initialize session manager.

        Args:
            session_file: Path to session file for cookie persistence
        """
        self.session_file = session_file
        self.loader: Optional[instaloader.Instaloader] = None
        self.username: Optional[str] = None

        logger.debug(f"Session manager initialized with session file: {session_file}")

    def create_loader(self) -> instaloader.Instaloader:
        """Create and configure Instaloader instance.

        Returns:
            Configured Instaloader instance
        """
        loader = instaloader.Instaloader(
            download_videos=False,  # We'll handle video downloads separately
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,  # We'll save our own metadata format
            compress_json=False,
            post_metadata_txt_pattern="",
            quiet=True,  # Reduce instaloader's own output
        )

        logger.debug("Instaloader instance created")
        return loader

    def login(self, username: str, password: str) -> bool:
        """Login to Instagram.

        Args:
            username: Instagram username
            password: Instagram password

        Returns:
            True if login successful, False otherwise
        """
        try:
            self.loader = self.create_loader()

            logger.info(f"Attempting to login as {username}")
            self.loader.login(username, password)

            self.username = username
            logger.info(f"Successfully logged in as {username}")

            # Save session
            self._save_session()

            return True

        except instaloader.exceptions.BadCredentialsException:
            logger.error("Invalid Instagram credentials")
            return False
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            logger.error("Two-factor authentication required - not currently supported")
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def load_session(self, username: str) -> bool:
        """Load existing session from file.

        Args:
            username: Instagram username

        Returns:
            True if session loaded successfully, False otherwise
        """
        try:
            self.loader = self.create_loader()

            if not self.session_file.exists():
                logger.warning(f"Session file not found: {self.session_file}")
                return False

            logger.info(f"Loading session for {username} from {self.session_file}")
            self.loader.load_session_from_file(username, self.session_file)

            self.username = username
            logger.info(f"Session loaded successfully for {username}")

            return True

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False

    def _save_session(self) -> None:
        """Save current session to file."""
        if not self.loader or not self.username:
            logger.warning("No active session to save")
            return

        try:
            # Create session directory if needed
            self.session_file.parent.mkdir(parents=True, exist_ok=True)

            self.loader.save_session_to_file(self.session_file)
            logger.info(f"Session saved to {self.session_file}")

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def authenticate(
        self, username: Optional[str] = None, password: Optional[str] = None
    ) -> bool:
        """Authenticate with Instagram using credentials or existing session.

        Args:
            username: Instagram username (optional if using saved session)
            password: Instagram password (optional if using saved session)

        Returns:
            True if authenticated successfully
        """
        # Try to use existing session first
        if username and self.load_session(username):
            return True

        # If no saved session or loading failed, try to login
        if username and password:
            return self.login(username, password)

        # No credentials provided and no saved session
        logger.warning("No authentication credentials or saved session available")
        logger.info("Proceeding without authentication (limited access to public profiles)")

        # Create unauthenticated loader
        self.loader = self.create_loader()
        return True

    def get_loader(self) -> instaloader.Instaloader:
        """Get Instaloader instance.

        Returns:
            Instaloader instance

        Raises:
            RuntimeError: If not authenticated
        """
        if not self.loader:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        return self.loader

    def is_authenticated(self) -> bool:
        """Check if session is authenticated.

        Returns:
            True if authenticated with username/password
        """
        return self.loader is not None and self.username is not None

    def logout(self) -> None:
        """Logout and clear session."""
        self.loader = None
        self.username = None
        logger.info("Logged out")
