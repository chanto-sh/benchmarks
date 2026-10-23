import math
import unittest

from heat import solve


def sine_profile(nx, length):
    return [math.sin(math.pi * i / (nx - 1)) for i in range(nx)]


class TestHeat(unittest.TestCase):
    def test_slow_rod(self):
        u = solve(sine_profile(21, 1.0), 0.01, 1.0, 0.5)
        expect = math.exp(-0.01 * math.pi ** 2 * 0.5)
        self.assertAlmostEqual(u[10], expect, places=3)

    def test_conductive_rod(self):
        u = solve(sine_profile(51, 1.0), 1.0, 1.0, 0.1)
        expect = math.exp(-math.pi ** 2 * 0.1)
        self.assertAlmostEqual(u[25], expect, places=3)


if __name__ == "__main__":
    unittest.main()
