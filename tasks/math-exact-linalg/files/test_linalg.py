import unittest
from fractions import Fraction

from linalg import det, rank, solve


class TestLinalg(unittest.TestCase):
    def test_det_exact(self):
        self.assertEqual(det([[2, 1], [1, 1]]), Fraction(1))
        self.assertIsInstance(det([[2, 1], [1, 1]]), Fraction)

    def test_det_needs_row_swap(self):
        self.assertEqual(det([[0, 1], [1, 0]]), Fraction(-1))

    def test_rank(self):
        self.assertEqual(rank([[1, 2, 3], [2, 4, 6], [1, 0, 1]]), 2)

    def test_solve(self):
        self.assertEqual(solve([[2, 0], [0, 4]], [1, 1]), [Fraction(1, 2), Fraction(1, 4)])

    def test_singular_solve(self):
        self.assertIsNone(solve([[1, 2], [2, 4]], [1, 2]))


if __name__ == "__main__":
    unittest.main()
