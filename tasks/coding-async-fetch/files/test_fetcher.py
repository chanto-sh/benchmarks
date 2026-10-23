import asyncio
import unittest

from fetcher import fetch_all


class FetcherTest(unittest.TestCase):
    def test_order(self):
        async def fetch(url):
            await asyncio.sleep(0.01 * (5 - int(url[-1])))
            return url.upper()
        urls = [f"http://x/{i}" for i in range(5)]
        self.assertEqual(asyncio.run(fetch_all(urls, fetch)), [u.upper() for u in urls])

    def test_failure_does_not_kill_batch(self):
        async def fetch(url):
            if url == "bad":
                raise ValueError(url)
            return 1
        res = asyncio.run(fetch_all(["a", "bad", "c"], fetch))
        self.assertEqual(res[0], 1)
        self.assertIsInstance(res[1], ValueError)
        self.assertEqual(res[2], 1)


if __name__ == "__main__":
    unittest.main()
