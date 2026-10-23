import math
import unittest

from roots import real_roots


class TestRoots(unittest.TestCase):
    def assertRoots(self, got, want):
        self.assertEqual(len(got), len(want), got)
        for g, w in zip(got, want):
            self.assertAlmostEqual(g, w, delta=1e-9)

    def test_three_simple_roots(self):
        # (x - 1)(x - 2)(x + 3) = x^3 - 7x + 6
        self.assertRoots(real_roots([1, 0, -7, 6], -5, 5), [-3, 1, 2])

    def test_irrational(self):
        self.assertRoots(real_roots([1, 0, -2], 0, 2), [math.sqrt(2)])

    def test_no_roots(self):
        self.assertEqual(real_roots([1, 0, 1], -10, 10), [])


if __name__ == "__main__":
    unittest.main()
