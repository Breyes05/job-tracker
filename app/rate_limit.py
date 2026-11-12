"""In-memory rate limiting for login attempts.

Counts are kept in this process's memory. That's fine with a single server, but
they reset on restart and aren't shared between servers; with more than one
instance, the counters would move to a shared store like Redis.
"""

import math
import time
from collections import defaultdict, deque


class RateLimiter:
    """Allow at most `max_attempts` per key within a sliding window of `window_seconds`."""

    def __init__(self, max_attempts: int, window_seconds: int, clock=time.monotonic):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        # A monotonic clock never jumps backward, even if the system time changes.
        self.clock = clock
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str) -> deque[float]:
        """Drop attempts that have fallen out of the window."""
        attempts = self._attempts[key]
        cutoff = self.clock() - self.window_seconds
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()
        if not attempts:
            # Don't keep empty entries around for every key ever seen.
            del self._attempts[key]
        return attempts

    def hit(self, key: str) -> None:
        """Record one attempt for this key."""
        self._prune(key)
        self._attempts[key].append(self.clock())

    def retry_after(self, key: str) -> int:
        """Seconds until this key may try again, or 0 if it isn't blocked."""
        attempts = self._prune(key)
        if len(attempts) < self.max_attempts:
            return 0
        # Blocked until the oldest attempt in the window expires.
        return max(1, math.ceil(attempts[0] + self.window_seconds - self.clock()))

    def reset(self, key: str) -> None:
        """Forget this key's attempts (after a successful login)."""
        self._attempts.pop(key, None)

    def clear(self) -> None:
        """Forget everything (used between tests)."""
        self._attempts.clear()


# Protects each account from password guessing.
failed_logins_by_email = RateLimiter(max_attempts=5, window_seconds=15 * 60)
# Stops one client from trying many accounts quickly.
login_attempts_by_ip = RateLimiter(max_attempts=20, window_seconds=60)
