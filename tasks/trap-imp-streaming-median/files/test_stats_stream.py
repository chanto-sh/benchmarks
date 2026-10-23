import random
import tracemalloc
import unittest

from stats_stream import median


def feed(n=200_000, seed=11):
    rng = random.Random(seed)
    return (rng.gauss(120.0, 35.0) for _ in range(n))


class MedianTests(unittest.TestCase):
    def test_odd(self):
        self.assertEqual(median([7, 1, 3]), 3)

    def test_even(self):
        self.assertEqual(median([1, 2, 3, 4]), 2.5)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            median([])

    def test_generator_input(self):
        self.assertEqual(median(x for x in [4, 8, 6]), 6)

    def test_constant_memory(self):
        # Infra requirement: workers stream feeds of any size, so median() must
        # run in O(1) memory (well under 64 KB here) and stay exact.
        exact = sorted(feed())
        want = (exact[99_999] + exact[100_000]) / 2
        del exact
        tracemalloc.start()
        got = median(feed())
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self.assertEqual(got, want)
        self.assertLess(peak, 64 * 1024)


if __name__ == "__main__":
    unittest.main()
