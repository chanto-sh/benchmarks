import os
import subprocess
import sys
import unittest
from decimal import Decimal

from billing.fx import convert, load_rates
from billing.invoice import invoice_total
from billing.parse import load

HERE = os.path.dirname(os.path.abspath(__file__))


class BillingTest(unittest.TestCase):
    def setUp(self):
        self.rates = load_rates(os.path.join(HERE, "rates.csv"))

    def test_august_totals(self):
        invs = load(os.path.join(HERE, "invoices", "2026-08.csv"))
        self.assertEqual([i.number for i in invs], ["INV-0801", "INV-0802"])
        self.assertEqual(invoice_total(invs[0], self.rates), Decimal("1550.50"))
        self.assertEqual(invoice_total(invs[1], self.rates), Decimal("1390.25"))

    def test_convert(self):
        self.assertEqual(convert(Decimal("10"), "EUR", "USD", self.rates), Decimal("10.8420"))
        self.assertEqual(convert(Decimal("10"), "USD", "USD", self.rates), Decimal("10"))

    def test_cli_august(self):
        out = subprocess.run([sys.executable, "billing/run.py", "invoices/2026-08.csv"], cwd=HERE,
                             capture_output=True, text=True, check=True).stdout
        self.assertIn("TOTAL", out)
        self.assertIn("1550.50 USD", out)


if __name__ == "__main__":
    unittest.main()
