"""HTTP client wrapper that respects the partner API's rate limit."""
import asyncio

from vendor.ratelimit import RateLimiter


class _ThreadedLimiter:
    """Runs the blocking limiter in a worker thread so async code can wait on it.
    Remove once ratelimit has native async support."""

    def __init__(self, limiter):
        self.limiter = limiter

    async def wait(self):
        await asyncio.get_running_loop().run_in_executor(None, self.limiter.acquire)


class Client:
    def __init__(self, fetch, limiter=None):
        self.fetch = fetch
        self.limiter = limiter or RateLimiter(10, 1.0)

    def fetch_all(self, urls):
        """Fetch each URL in order, waiting for the limiter before each request."""
        out = []
        for url in urls:
            self.limiter.acquire()
            out.append(self.fetch(url))
        return out
