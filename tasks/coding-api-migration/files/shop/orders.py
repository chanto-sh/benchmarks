from .db import query
from .inventory import reserve


def place_order(customer_id, items, placed_at):
    """items: [(sku, qty)]. Reserves stock, records the order at current prices; returns the order id."""
    for sku, qty in items:
        reserve(sku, qty)
    query("INSERT INTO orders (customer_id, placed_at) VALUES (%s, %s)", customer_id, placed_at)
    order_id = query("SELECT last_insert_rowid()")[0][0]
    for sku, qty in items:
        price = query("SELECT price_cents FROM products WHERE sku = %s", sku)[0][0]
        query("INSERT INTO order_lines (order_id, sku, qty, price_cents) VALUES (%s, %s, %s, %s)", order_id, sku, qty, price)
    return order_id


def order_total(order_id):
    """Total in cents."""
    rows = query("SELECT qty, price_cents FROM order_lines WHERE order_id = %s", order_id)
    return sum(r[0] * r[1] for r in rows)


def recent_orders(customer_id, limit=5):
    """The customer's latest orders, newest first, as (order_id, placed_at)."""
    return query("SELECT id, placed_at FROM orders WHERE customer_id = %s ORDER BY placed_at DESC, id DESC LIMIT %s",
                 customer_id, limit)
