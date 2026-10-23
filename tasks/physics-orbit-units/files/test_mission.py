import unittest

from mission import hohmann_dv


class TestMission(unittest.TestCase):
    def test_leo_to_geo(self):
        # 200 km parking orbit to geostationary altitude: about 3.94 km/s
        self.assertAlmostEqual(hohmann_dv(200.0, 35786.0), 3.94, delta=0.01)


if __name__ == "__main__":
    unittest.main()
