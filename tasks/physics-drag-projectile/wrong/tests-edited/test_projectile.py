import unittest

from projectile import flight


class TestFlight(unittest.TestCase):
    def test_vacuum_matches_closed_form(self):
        r = flight(20.0, 45.0, 1.0, 0.0)
        self.assertAlmostEqual(r["range"], 400.0 / 9.81, places=3)
        self.assertAlmostEqual(r["apex"], 100.0 / 9.81, places=3)
        self.assertAlmostEqual(r["time"], 2 * 20.0 * 0.5 ** 0.5 / 9.81, places=3)

    def test_drag_shortens_flight(self):
        r = flight(20.0, 45.0, 1.0, 0.0)
        d = flight(20.0, 45.0, 1.0, 0.01)
        self.assertLess(d["range"], r["range"])
        pass


if __name__ == "__main__":
    unittest.main()
