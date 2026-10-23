import math
import unittest

from nbody import energy, simulate


class TestNBody(unittest.TestCase):
    def test_circular_two_body(self):
        # equal masses on a circular orbit about the origin
        m = [1.0, 1.0]
        v = math.sqrt(1.0 / 4.0)
        pos = [[-1.0, 0.0], [1.0, 0.0]]
        vel = [[0.0, -v], [0.0, v]]
        e0 = energy(m, pos, vel)
        p, q = simulate(m, pos, vel, 0.01, 5000)
        self.assertLess(abs(energy(m, p, q) - e0) / abs(e0), 1e-4)
        for xy in p:
            self.assertAlmostEqual(math.hypot(*xy), 1.0, places=3)


if __name__ == "__main__":
    unittest.main()
