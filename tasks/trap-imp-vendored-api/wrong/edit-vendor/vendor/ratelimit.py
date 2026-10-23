"""Token-bucket rate limiter.

Synced from platform-libs (ratelimit 2.4.1). Do not edit by hand: changes go
upstream and are pulled in with `make vendor`.
"""
import threading
import time

__version__ = "2.4.1"


class RateLimiter:
    """Allow `rate` acquisitions per `per` seconds, with bursts up to `rate`."""

    def __init__(self, rate, per=1.0, clock=time.monotonic, sleep=time.sleep):
        if rate <= 0 or per <= 0:
            raise ValueError("rate and per must be positive")
        self.rate = rate
        self.per = per
        self._clock = clock
        self._sleep = sleep
        self._tokens = float(rate)
        self._last = clock()
        self._lock = threading.Lock()

    def _refill(self):
        now = self._clock()
        self._tokens = min(self.rate, self._tokens + (now - self._last) * self.rate / self.per)
        self._last = now

    def try_acquire(self):
        """Take a token if one is available; never blocks."""
        with self._lock:
            self._refill()
            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False

    def acquire(self):
        """Block until a token is available, then take it."""
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait = (1 - self._tokens) * self.per / self.rate
            self._sleep(wait)

    async def acquire_async(self):
        self.acquire()
