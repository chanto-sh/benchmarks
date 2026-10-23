import unittest
from fractions import Fraction

from odds import p_at_least


class TestOdds(unittest.TestCase):
    def test_one_red_before_green(self):
        # orders RRG, RGR, GRR: a red comes first in two of three
        self.assertEqual(p_at_least(2, 0, 1, 1, 10), Fraction(2, 3))

    def test_both_reds_before_green(self):
        self.assertEqual(p_at_least(2, 0, 1, 2, 10), Fraction(4, 9))

    def test_zero_needed(self):
        self.assertEqual(p_at_least(3, 3, 3, 0, 4), Fraction(1))


if __name__ == "__main__":
    unittest.main()
