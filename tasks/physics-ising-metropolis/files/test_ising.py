import random
import unittest

from ising import delta_energy, energy


class TestIsing(unittest.TestCase):
    def test_ground_state_energy(self):
        spins = [[1] * 4 for _ in range(4)]
        # 16 sites x 2 bonds each on a periodic lattice
        self.assertEqual(energy(spins), -32.0)

    def test_delta_matches_energy_difference(self):
        rng = random.Random(3)
        spins = [[rng.choice((-1, 1)) for _ in range(5)] for _ in range(5)]
        for i, j in [(0, 0), (2, 3), (4, 4)]:
            before = energy(spins)
            d = delta_energy(spins, i, j)
            spins[i][j] *= -1
            self.assertAlmostEqual(energy(spins) - before, d)
            spins[i][j] *= -1


if __name__ == "__main__":
    unittest.main()
