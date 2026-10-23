import unittest

from shop import db, schema
from shop.customers import add_customer, customers_by_tier, find_customer
from shop.inventory import OutOfStock, reserve, search_products, stock
from shop.orders import order_total, place_order, recent_orders
from shop.reports import best_sellers, revenue_by_tier


class ShopTest(unittest.TestCase):
    def setUp(self):
        d = db.connect()
        schema.init(d)
        d.execute("INSERT INTO products VALUES ('MUG', 'Coffee mug', 1200, 10), ('TEE', 'T-shirt', 2500, 3)")

    def test_flow(self):
        cid = add_customer("Ada", "ada@example.com", "gold")
        self.assertEqual(find_customer("ADA@example.com"), {"id": cid, "name": "Ada", "email": "ada@example.com", "tier": "gold"})
        oid = place_order(cid, [("MUG", 2), ("TEE", 1)], "2026-10-01")
        self.assertEqual(order_total(oid), 4900)
        self.assertEqual(stock("MUG"), 8)
        self.assertEqual(recent_orders(cid), [(oid, "2026-10-01")])
        self.assertEqual(revenue_by_tier(), [("gold", 4900)])
        self.assertEqual(best_sellers(1), [("MUG", 2)])

    def test_out_of_stock(self):
        cid = add_customer("Bob", "bob@example.com")
        with self.assertRaises(OutOfStock):
            reserve("TEE", 4)
        self.assertEqual(stock("TEE"), 3)
        self.assertEqual(customers_by_tier("basic"), ["Bob"])
        self.assertEqual(search_products("mug"), [("MUG", "Coffee mug")])


if __name__ == "__main__":
    unittest.main()
