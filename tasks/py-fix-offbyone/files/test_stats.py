import unittest
from stats import moving_average, median


class TestStats(unittest.TestCase):
    def test_moving_average(self):
        self.assertEqual(moving_average([1, 2, 3, 4], 2), [1.5, 2.5, 3.5])
        self.assertEqual(moving_average([5], 1), [5.0])
        self.assertEqual(moving_average([1, 2], 3), [])

    def test_median(self):
        self.assertEqual(median([3, 1, 2]), 2)
        self.assertEqual(median([4, 1, 3, 2]), 2.5)

    def test_bad_k(self):
        with self.assertRaises(ValueError):
            moving_average([1], 0)


if __name__ == "__main__":
    unittest.main()
