import math
import unittest

from stats import logsumexp, mean_var, softplus


class TestStats(unittest.TestCase):
    def test_variance_with_offset(self):
        xs = [1e9 + d for d in (4.0, 7.0, 13.0, 16.0)]
        m, v = mean_var(xs)
        self.assertAlmostEqual(m, 1e9 + 10.0, delta=1e-6)
        self.assertAlmostEqual(v, 22.5, delta=1e-6)

    def test_logsumexp_large(self):
        self.assertAlmostEqual(logsumexp([1000.0, 1000.0]), 1000.0 + math.log(2), delta=1e-9)

    def test_softplus_large(self):
        self.assertEqual(softplus(1000.0), 1000.0)


if __name__ == "__main__":
    unittest.main()
