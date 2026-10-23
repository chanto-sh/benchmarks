import unittest
from fractions import Fraction

from game import expected_turns


class TestExpectedTurns(unittest.TestCase):
    def test_one_sided_die_walks(self):
        self.assertEqual(expected_turns(3, 1), Fraction(3))

    def test_small_board(self):
        self.assertEqual(expected_turns(4, 2), Fraction(7, 2))

    def test_exact_type(self):
        self.assertIsInstance(expected_turns(5, 3), Fraction)


if __name__ == "__main__":
    unittest.main()
