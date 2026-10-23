import os
import unittest
from unittest import mock

os.environ.setdefault("ORDERS_DB_URL", ":memory:")
os.environ.setdefault("ORDERS_TEST_MODE", "1")

from app.orders import service  # noqa: E402


class OrdersTest(unittest.TestCase):
    def test_open_orders_uses_customer(self):
        with mock.patch("app.orders.service.query_raw", return_value=[(1, 9)]) as q:
            self.assertEqual(service.open_orders(7), [(1, 9)])
        self.assertEqual(q.call_args[0][1], 7)


if __name__ == "__main__":
    unittest.main()
