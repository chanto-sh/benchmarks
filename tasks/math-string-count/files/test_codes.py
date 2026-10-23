import unittest

from codes import count_codes


class TestCountCodes(unittest.TestCase):
    def test_single_letter(self):
        # "A" and "B"; "C" has one C, not a multiple of 3
        self.assertEqual(count_codes(1), 2)

    def test_three(self):
        self.assertEqual(count_codes(3), 6)

    def test_thirty(self):
        self.assertEqual(count_codes(30), 795051511)


if __name__ == "__main__":
    unittest.main()
