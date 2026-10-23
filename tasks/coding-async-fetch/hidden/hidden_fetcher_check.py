import asyncio
import unittest

from fetcher import fetch_all


class Probe:
    def __init__(self, fail_times=None, delay=lambda u: 0.002):
        self.inflight = 0
        self.max_inflight = 0
        self.calls = {}
        self.fail_times = fail_times or {}
        self.delay = delay

    async def __call__(self, url):
        self.calls[url] = self.calls.get(url, 0) + 1
        self.inflight += 1
        self.max_inflight = max(self.max_inflight, self.inflight)
        try:
            await asyncio.sleep(self.delay(url))
            if self.calls[url] <= self.fail_times.get(url, 0):
                raise ConnectionError(f"{url} attempt {self.calls[url]}")
            return f"<{url}>"
        finally:
            self.inflight -= 1


class HiddenFetcher(unittest.TestCase):
    def test_limit_is_respected_and_used(self):
        for limit, n in [(3, 23), (1, 6), (7, 40), (10, 4)]:
            p = Probe(delay=lambda u: 0.001 * (int(u[1:]) % 4 + 1))
            urls = [f"u{i}" for i in range(n)]
            res = asyncio.run(fetch_all(urls, p, limit=limit))
            self.assertEqual(res, [f"<{u}>" for u in urls])
            self.assertEqual(p.max_inflight, min(limit, n), (limit, n))

    def test_retries(self):
        p = Probe(fail_times={"a": 2, "b": 3, "c": 1, "d": 99})
        res = asyncio.run(fetch_all(["a", "b", "c", "d", "e"], p, limit=2, retries=2))
        self.assertEqual(res[0], "<a>")
        self.assertIsInstance(res[1], ConnectionError)
        self.assertEqual(str(res[1]), "b attempt 3")
        self.assertEqual(res[2], "<c>")
        self.assertEqual(str(res[3]), "d attempt 3")
        self.assertEqual(res[4], "<e>")
        self.assertEqual(p.calls, {"a": 3, "b": 3, "c": 2, "d": 3, "e": 1})
        self.assertLessEqual(p.max_inflight, 2)

    def test_no_retries(self):
        p = Probe(fail_times={"x": 1})
        res = asyncio.run(fetch_all(["x", "y"], p, retries=0))
        self.assertEqual(str(res[0]), "x attempt 1")
        self.assertEqual(res[1], "<y>")
        self.assertEqual(p.calls, {"x": 1, "y": 1})

    def test_duplicates_and_empty(self):
        self.assertEqual(asyncio.run(fetch_all([], Probe())), [])
        p = Probe(delay=lambda u: 0.001)
        self.assertEqual(asyncio.run(fetch_all(["q", "q", "r"], p, limit=2)), ["<q>", "<q>", "<r>"])
        self.assertEqual(p.calls, {"q": 2, "r": 1})


if __name__ == "__main__":
    unittest.main()
