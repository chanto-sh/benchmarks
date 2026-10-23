SCHEMA = """
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, tier TEXT NOT NULL);
CREATE TABLE products (sku TEXT PRIMARY KEY, name TEXT NOT NULL, price_cents INTEGER NOT NULL, stock INTEGER NOT NULL);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL, placed_at TEXT NOT NULL);
CREATE TABLE order_lines (order_id INTEGER NOT NULL, sku TEXT NOT NULL, qty INTEGER NOT NULL, price_cents INTEGER NOT NULL);
"""


def init(db):
    db.executescript(SCHEMA)
