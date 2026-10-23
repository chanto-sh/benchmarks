from .db import get
from .inventory import reserve


def place_order(customer_id, items, placed_at):
    """items: [(sku, qty)]. Reserves stock, records the order at current prices; returns the order id."""
    db = get()
    for sku, qty in items:
        reserve(sku, qty)
    db.execute("INSERT INTO orders (customer_id, placed_at) VALUES (?, ?)", (customer_id, placed_at))
    order_id = db.fetch_one("SELECT last_insert_rowid() AS id")["id"]
    for sku, qty in items:
        price = db.fetch_one("SELECT price_cents FROM products WHERE sku = ?", (sku,))["price_cents"]
        db.execute("INSERT INTO order_lines (order_id, sku, qty, price_cents) VALUES (?, ?, ?, ?)",
                   (order_id, sku, qty, price))
    return order_id


def order_total(order_id):
    """Total in cents."""
    rows = get().fetch_all("SELECT qty, price_cents FROM order_lines WHERE order_id = ?", (order_id,))
    return sum(r["qty"] * r["price_cents"] for r in rows)


def recent_orders(customer_id, limit=5):
    """The customer's latest orders, newest first, as (order_id, placed_at)."""
    rows = get().fetch_all("SELECT id, placed_at FROM orders WHERE customer_id = ? ORDER BY placed_at DESC, id DESC LIMIT ?",
                           (customer_id, limit))
    return [(r["id"], r["placed_at"]) for r in rows]
