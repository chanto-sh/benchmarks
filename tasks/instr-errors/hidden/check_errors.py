import unittest

from ledger import Book, LedgerError


class Rejects(unittest.TestCase):
    def check(self, src, dst, amount):
        b = Book({"a": 10, "b": 5})
        with self.assertRaises(Exception) as cm:
            b.transfer(src, dst, amount)
        self.assertIsInstance(cm.exception, LedgerError, f"AGENTS.md: raise LedgerError subclasses, got {type(cm.exception).__name__}")
        self.assertIsNot(type(cm.exception), LedgerError, "use a specific subclass")
        self.assertEqual(b.balances, {"a": 10, "b": 5})

    def test_zero(self):
        self.check("a", "b", 0)

    def test_negative(self):
        self.check("a", "b", -3)

    def test_self(self):
        self.check("a", "a", 2)

    def test_valid_still_works(self):
        b = Book({"a": 10, "b": 5})
        b.transfer("a", "b", 10)
        self.assertEqual(b.balances, {"a": 0, "b": 15})


if __name__ == "__main__":
    unittest.main()
