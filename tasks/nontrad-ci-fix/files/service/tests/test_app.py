import unittest
from decimal import Decimal

from app import pricing, version
from app.config import load_settings


class AppTests(unittest.TestCase):
    def test_settings_are_ci(self):
        self.assertEqual(load_settings().DATABASE_URL, "memory://")

    def test_total(self):
        self.assertEqual(pricing.total([("10.00", 2), ("0.99", 1)]), Decimal("22.67"))

    def test_version(self):
        self.assertIn("(ci)", version.version_string())


if __name__ == "__main__":
    unittest.main()
