import math
import unittest

from orbit import newtonian, radial_period


class TestOrbit(unittest.TestCase):
    def test_kepler_ellipse_from_periapsis(self):
        # GM = 1, periapsis 0.5, eccentricity 0.5 -> a = 1, period 2 pi
        v = math.sqrt((1 + 0.5) / 0.5)
        t = radial_period((0.5, 0.0), (0.0, v), newtonian(1.0))
        self.assertAlmostEqual(t / (2 * math.pi), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
