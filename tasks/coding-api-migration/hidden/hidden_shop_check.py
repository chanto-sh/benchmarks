import unittest

from shop import db, schema
from shop.customers import add_customer, customers_by_tier, find_customer
from shop.inventory import OutOfStock, reserve, search_products, stock
from shop.orders import order_total, place_order, recent_orders
from shop.reports import best_sellers, revenue_by_tier


class HiddenShop(unittest.TestCase):
    def setUp(self):
        d = db.connect()
        schema.init(d)
        d.execute("INSERT INTO products VALUES ('A1', 'Blue 100% cotton tee', 1999, 5), ('B2', 'Mug 50%% off', 800, 2), "
                  "('C3', 'Poster', 1500, 0), ('D4', 'Sticker', 150, 100)")

    def test_everything(self):
        x = add_customer("Xia", "Xia@Example.com", "silver")
        y = add_customer("Yan", "yan@example.com", "gold")
        z = add_customer("Abe", "abe@example.com", "silver")
        self.assertNotEqual(x, y)
        self.assertIsNone(find_customer("nobody@example.com"))
        self.assertEqual(find_customer("xia@example.COM")["id"], x)
        self.assertEqual(customers_by_tier("silver"), ["Abe", "Xia"])
        self.assertEqual(customers_by_tier("platinum"), [])
        self.assertEqual(search_products("100%"), [("A1", "Blue 100% cotton tee")])
        self.assertEqual(search_products("MUG"), [("B2", "Mug 50%% off")])
        self.assertEqual(search_products("zzz"), [])
        self.assertEqual(stock("NOPE"), 0)
        with self.assertRaises(OutOfStock):
            reserve("C3", 1)
        with self.assertRaises(OutOfStock):
            reserve("NOPE", 1)
        o1 = place_order(x, [("A1", 2), ("D4", 10)], "2026-09-01")
        o2 = place_order(y, [("B2", 2)], "2026-09-03")
        o3 = place_order(x, [("D4", 1)], "2026-09-02")
        o4 = place_order(z, [("A1", 1)], "2026-09-02")
        with self.assertRaises(OutOfStock):
            place_order(y, [("B2", 1)], "2026-09-04")
        self.assertEqual(stock("B2"), 0)
        self.assertEqual(order_total(o1), 2 * 1999 + 10 * 150)
        self.assertEqual(order_total(999), 0)
        self.assertEqual(recent_orders(x), [(o3, "2026-09-02"), (o1, "2026-09-01")])
        self.assertEqual(recent_orders(x, limit=1), [(o3, "2026-09-02")])
        self.assertEqual(recent_orders(12345), [])
        r = revenue_by_tier()
        self.assertEqual(r, [("silver", 2 * 1999 + 10 * 150 + 150 + 1999), ("gold", 1600)])
        self.assertTrue(all(type(t) is tuple for t in r))
        b = best_sellers()
        self.assertEqual(b, [("D4", 11), ("A1", 3), ("B2", 2)])
        self.assertTrue(all(type(t) is tuple for t in b))
        self.assertTrue(all(type(t) is tuple for t in recent_orders(x)))
        self.assertTrue(all(type(t) is tuple for t in search_products("o")))


if __name__ == "__main__":
    unittest.main()
