import unittest
from datetime import date

from workdays import business_days

MON, FRI, SAT, NEXT_MON = date(2026, 10, 5), date(2026, 10, 9), date(2026, 10, 10), date(2026, 10, 12)


class BusinessDays(unittest.TestCase):
    def test_same_day_is_zero(self):
        self.assertEqual(business_days(MON, MON), 0)

    def test_end_is_exclusive(self):
        self.assertEqual(business_days(MON, FRI), 4)

    def test_over_weekend(self):
        self.assertEqual(business_days(FRI, NEXT_MON), 1)
        self.assertEqual(business_days(MON, NEXT_MON), 5)

    def test_holidays(self):
        self.assertEqual(business_days(MON, NEXT_MON, holidays=[date(2026, 10, 7)]), 4)
        # A holiday on a weekend doesn't count twice.
        self.assertEqual(business_days(MON, NEXT_MON, holidays=[SAT]), 5)

    def test_reversed_range_is_negative(self):
        self.assertEqual(business_days(NEXT_MON, MON), -5)


if __name__ == "__main__":
    unittest.main()
