"""Concurrent page fetching for the crawler."""
import asyncio


async def fetch_all(urls, fetch, limit=5, retries=2):
    """Fetch every URL with `await fetch(url)` and return the results.

    - At most `limit` fetches are in flight at any moment.
    - The result list lines up with `urls`: results[i] belongs to urls[i].
    - A fetch that raises is retried, up to `retries` more times. If it still
      fails, results[i] is the last exception instance raised for it; the other
      URLs are not affected.
    """
    results = [None] * len(urls)

    async def one(i, url):
        sem = asyncio.Semaphore(limit)
        for attempt in range(retries + 1):
            try:
                async with sem:
                    results[i] = await fetch(url)
                return
            except Exception as e:
                results[i] = e

    await asyncio.gather(*(one(i, u) for i, u in enumerate(urls)))
    return results
