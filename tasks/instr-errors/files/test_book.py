import unittest

from ledger import Book, UnknownAccount


class BookTest(unittest.TestCase):
    def test_transfer(self):
        b = Book({"a": 10, "b": 0})
        b.transfer("a", "b", 4)
        self.assertEqual((b.balance("a"), b.balance("b")), (6, 4))

    def test_unknown(self):
        with self.assertRaises(UnknownAccount):
            Book({"a": 1}).transfer("a", "zz", 1)


if __name__ == "__main__":
    unittest.main()
