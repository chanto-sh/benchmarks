import math
import unittest

from chain import energy, simulate


class TestChain(unittest.TestCase):
    def test_energy_conserved(self):
        n = 8
        x0 = [0.3 * math.sin(math.pi * (i + 1) / (n + 1)) for i in range(n)]
        v0 = [0.0] * n
        masses = [1.0] * n
        e0 = energy(x0, v0, masses, 1.0, 0.5)
        x, v = simulate(x0, v0, masses, 1.0, 0.5, 0.02, 20000)
        self.assertLess(abs(energy(x, v, masses, 1.0, 0.5) - e0) / e0, 1e-4)


if __name__ == "__main__":
    unittest.main()
