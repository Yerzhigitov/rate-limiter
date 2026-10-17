"""Rate limiter'ы: Token Bucket и Sliding Window Log, плюс декоратор для функций."""
import functools
import threading
import time
from collections import defaultdict, deque


class TokenBucket:
    def __init__(self, capacity: int, refill_per_sec: float, clock=time.monotonic):
        self.capacity, self.rate, self.clock = capacity, refill_per_sec, clock
        self._tokens = defaultdict(lambda: float(capacity))
        self._last = {}
        self._lock = threading.Lock()

    def allow(self, client: str) -> bool:
        with self._lock:
            now = self.clock()
            elapsed = now - self._last.get(client, now)
            self._last[client] = now
            tokens = min(self.capacity, self._tokens[client] + elapsed * self.rate)
            if tokens >= 1:
                self._tokens[client] = tokens - 1
                return True
            self._tokens[client] = tokens
            return False


class SlidingWindow:
    def __init__(self, limit: int, window_sec: float, clock=time.monotonic):
        self.limit, self.window, self.clock = limit, window_sec, clock
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client: str) -> bool:
        with self._lock:
            now, hits = self.clock(), self._hits[client]
            while hits and hits[0] <= now - self.window:
                hits.popleft()
            if len(hits) < self.limit:
                hits.append(now)
                return True
            return False


class RateLimitExceeded(Exception):
    pass


def rate_limited(limiter, key_func=lambda *a, **k: "global"):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not limiter.allow(key_func(*args, **kwargs)):
                raise RateLimitExceeded(fn.__name__)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
