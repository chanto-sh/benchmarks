import math
import unittest

from oscillator import amplitude, displacement


class TestOscillator(unittest.TestCase):
    def test_amplitude_light_damping(self):
        # m=1, k=4, c=0.2, driven at omega=1: F0 / sqrt((k - m w^2)^2 + (c w)^2)
        self.assertAlmostEqual(amplitude(1.0, 4.0, 0.2, 1.0, 1.0), 1.0 / math.sqrt(9.0 + 0.04), places=9)

    def test_initial_conditions(self):
        self.assertAlmostEqual(displacement(1.0, 4.0, 0.2, 1.0, 1.0, 0.3, 0.0, 0.0), 0.3, places=9)

    def test_settles_to_steady_state(self):
        a = amplitude(1.0, 4.0, 0.5, 1.0, 1.0)
        late = [abs(displacement(1.0, 4.0, 0.5, 1.0, 1.0, 0.3, 0.0, 60 + 0.05 * i)) for i in range(130)]
        self.assertAlmostEqual(max(late), a, places=3)


if __name__ == "__main__":
    unittest.main()
