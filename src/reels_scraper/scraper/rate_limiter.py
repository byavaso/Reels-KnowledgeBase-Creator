"""Rate limiter for Instagram API requests."""

import time
from datetime import datetime, timedelta
from typing import Optional

from ..logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter to prevent hitting Instagram rate limits."""

    def __init__(self, delay: float = 2.0, max_requests_per_minute: int = 30):
        """Initialize rate limiter.

        Args:
            delay: Minimum delay between requests in seconds
            max_requests_per_minute: Maximum requests allowed per minute
        """
        self.delay = delay
        self.max_requests_per_minute = max_requests_per_minute
        self.last_request_time: Optional[datetime] = None
        self.request_times: list[datetime] = []

        logger.debug(
            f"Rate limiter initialized: {delay}s delay, "
            f"{max_requests_per_minute} requests/minute max"
        )

    def wait_if_needed(self) -> None:
        """Wait if necessary to comply with rate limits."""
        current_time = datetime.now()

        # Remove request times older than 1 minute
        cutoff_time = current_time - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff_time]

        # Check if we've exceeded requests per minute
        if len(self.request_times) >= self.max_requests_per_minute:
            # Wait until the oldest request is more than 1 minute old
            wait_until = self.request_times[0] + timedelta(minutes=1)
            wait_seconds = (wait_until - current_time).total_seconds()

            if wait_seconds > 0:
                logger.warning(
                    f"Rate limit approaching, waiting {wait_seconds:.1f}s before next request"
                )
                time.sleep(wait_seconds)
                current_time = datetime.now()

        # Check minimum delay between requests
        if self.last_request_time:
            elapsed = (current_time - self.last_request_time).total_seconds()
            if elapsed < self.delay:
                wait_time = self.delay - elapsed
                logger.debug(f"Waiting {wait_time:.2f}s before next request")
                time.sleep(wait_time)
                current_time = datetime.now()

        # Record this request
        self.last_request_time = current_time
        self.request_times.append(current_time)

    def __enter__(self) -> "RateLimiter":
        """Enter context manager."""
        self.wait_if_needed()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        pass

    def reset(self) -> None:
        """Reset rate limiter state."""
        self.last_request_time = None
        self.request_times = []
        logger.debug("Rate limiter reset")
