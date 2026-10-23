import unittest

from detector import response


class TestResponse(unittest.TestCase):
    def test_zero_frequency_is_two_sqrt_b(self):
        self.assertAlmostEqual(response(0, 4), 4.0, delta=1e-9)

    def test_unit(self):
        self.assertAlmostEqual(response(1, 1), 1.809048475800544, delta=1e-9)


if __name__ == "__main__":
    unittest.main()
