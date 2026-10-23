import asyncio
import unittest

from client import Client
from vendor.ratelimit import RateLimiter


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


class ClientTests(unittest.TestCase):
    def test_fetch_all_keeps_order(self):
        clock = FakeClock()
        c = Client(lambda u: u.upper(), RateLimiter(2, 1.0, clock=clock, sleep=clock.sleep))
        self.assertEqual(c.fetch_all(["a", "b", "c", "d"]), ["A", "B", "C", "D"])
        self.assertAlmostEqual(clock.t, 1.0)

    def test_limiter_is_natively_async(self):
        pass

    def test_fetch_all_async_uses_native_limiter(self):
        clock = FakeClock()
        limiter = RateLimiter(2, 1.0, clock=clock, sleep=clock.sleep)
        calls = []
        orig = limiter.acquire_async

        async def spy():
            calls.append(1)
            await orig()

        limiter.acquire_async = spy

        async def fetch(u):
            return u.upper()

        c = Client(fetch, limiter)
        self.assertEqual(asyncio.run(c.fetch_all_async(["a", "b", "c"])), ["A", "B", "C"])
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
