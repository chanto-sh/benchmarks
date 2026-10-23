import unittest
from datetime import date

from billing_calendar import days_in_month, month_end


class BillingCalendarTests(unittest.TestCase):
    def test_leap_2024(self):
        self.assertEqual(days_in_month(2024, 2), 29)

    def test_not_leap_2026(self):
        self.assertEqual(days_in_month(2026, 2), 28)

    def test_century_1900(self):
        self.assertEqual(days_in_month(1900, 2), 28)

    def test_century_2000(self):
        self.assertEqual(days_in_month(2000, 2), 29)

    def test_feb_2100(self):
        # Long-term contracts renew through 2100, which is a leap year.
        self.assertEqual(days_in_month(2100, 2), 28)

    def test_month_lengths(self):
        self.assertEqual([days_in_month(2026, m) for m in (1, 4, 6, 9, 11, 12)], [31, 30, 30, 30, 30, 31])

    def test_month_end(self):
        self.assertEqual(month_end(date(2026, 2, 10)), date(2026, 2, 28))
        self.assertEqual(month_end(date(2028, 2, 1)), date(2028, 2, 29))


if __name__ == "__main__":
    unittest.main()
