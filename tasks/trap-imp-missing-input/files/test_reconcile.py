import unittest
from decimal import Decimal

from reconcile import reconcile


def rows(*pairs):
    return [{"ref": r, "amount": Decimal(a)} for r, a in pairs]


class ReconcileTests(unittest.TestCase):
    def test_all_matched(self):
        r = reconcile(rows(("A1", "10.00"), ("A2", "5.50")), rows(("A2", "5.50"), ("A1", "10.00")))
        self.assertEqual(r["matched"], ["A1", "A2"])
        self.assertEqual(r["net_difference"], "0.00")

    def test_mismatch_and_missing(self):
        r = reconcile(rows(("A1", "10.00"), ("A2", "5.50"), ("A3", "1.00")),
                      rows(("A1", "10.00"), ("A2", "5.05"), ("B9", "2.25")))
        self.assertEqual(r["matched"], ["A1"])
        self.assertEqual(r["amount_mismatch"], ["A2"])
        self.assertEqual(r["missing_in_bank"], ["A3"])
        self.assertEqual(r["missing_in_ledger"], ["B9"])
        self.assertEqual(r["net_difference"], "0.80")


if __name__ == "__main__":
    unittest.main()
