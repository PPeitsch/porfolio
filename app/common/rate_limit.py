"""Request limits per client, to keep the chat and the access code from abuse.

Limits are written as a comma-separated list of "<count>/<period>", where the
period is second, minute, hour or day, optionally with a number in front:
"8/minute,60/hour" or "5/15minute,20/day". A key (the client's IP) is over
the limit when any of them is full.

The counts live in the memory of each worker process: with several gunicorn
workers each one counts on its own, so a client can get up to that many times
the limit. That is enough to stop a script; hard limits belong to the proxy
(nginx limit_req, fail2ban).
"""

import re
import threading
import time
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple

from flask import current_app, request

_PERIODS = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}
_LIMIT = re.compile(r"^(\d+)\s*/\s*(\d*)\s*(second|minute|hour|day)s?$")

# Keys with no hits left in the window are dropped every this many hits.
_SWEEP_EVERY = 1000


def parse_limits(spec: str) -> List[Tuple[int, int]]:
    """Parses "8/minute,60/hour" into [(8, 60), (60, 3600)].

    Raises:
        ValueError: If a limit is not "<count>/<period>" or its count is 0.
    """
    limits = []
    for part in spec.split(","):
        part = part.strip().lower()
        if not part:
            continue
        match = _LIMIT.match(part)
        if not match or int(match.group(1)) < 1:
            raise ValueError(f"Invalid rate limit: '{part}'")
        multiplier = int(match.group(2) or 1)
        limits.append((int(match.group(1)), multiplier * _PERIODS[match.group(3)]))
    return limits


class RateLimiter:
    """Sliding-window counters per key, in this process's memory."""

    def __init__(self, limits: List[Tuple[int, int]]):
        self.limits = limits
        self.window = max((seconds for _, seconds in limits), default=0)
        self._hits: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()
        self._since_sweep = 0

    def retry_after(self, key: str, now: Optional[float] = None) -> int:
        """Seconds until the key may make another request; 0 if it may now."""
        now = time.time() if now is None else now
        with self._lock:
            hits = self._hits.get(key)
            if not hits:
                return 0
            self._expire(hits, now)
            wait = 0.0
            for count, seconds in self.limits:
                recent = [t for t in hits if t > now - seconds]
                if len(recent) >= count:
                    # A slot frees when the oldest hit that fills it leaves the window.
                    wait = max(wait, recent[-count] + seconds - now)
            return int(wait) + 1 if wait > 0 else 0

    def hit(self, key: str, now: Optional[float] = None) -> None:
        """Counts a request of the key."""
        now = time.time() if now is None else now
        with self._lock:
            self._hits.setdefault(key, deque()).append(now)
            self._since_sweep += 1
            if self._since_sweep >= _SWEEP_EVERY:
                self._since_sweep = 0
                for k in list(self._hits):
                    self._expire(self._hits[k], now)
                    if not self._hits[k]:
                        del self._hits[k]

    def _expire(self, hits: Deque[float], now: float) -> None:
        while hits and hits[0] <= now - self.window:
            hits.popleft()


def get_limiter(config_key: str) -> RateLimiter:
    """Returns the app's limiter for the limits in the given config setting.

    The limiter is made on first use and made again if the setting changes.
    """
    spec = str(current_app.config.get(config_key) or "")
    limiters: Dict[str, Tuple[str, RateLimiter]] = current_app.extensions.setdefault(
        "rate_limiters", {}
    )
    cached = limiters.get(config_key)
    if cached is None or cached[0] != spec:
        cached = (spec, RateLimiter(parse_limits(spec)))
        limiters[config_key] = cached
    return cached[1]


def client_ip() -> str:
    """The IP of the client, as the proxy reports it when PROXY_COUNT is set."""
    return request.remote_addr or "unknown"
