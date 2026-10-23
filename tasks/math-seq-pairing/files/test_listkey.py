import unittest

from listkey import decode, encode


class TestListKey(unittest.TestCase):
    def test_round_trip(self):
        for lst in ([], [0], [0, 0], [5], [1, 2, 3], [10, 0, 7]):
            self.assertEqual(decode(encode(lst)), lst)

    def test_every_small_key_is_valid(self):
        for n in range(200):
            self.assertEqual(encode(decode(n)), n)

    def test_types(self):
        self.assertIsInstance(encode([3, 4]), int)
        self.assertIsInstance(decode(17), list)


if __name__ == "__main__":
    unittest.main()
