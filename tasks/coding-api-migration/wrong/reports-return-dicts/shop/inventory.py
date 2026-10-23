from .db import get


class OutOfStock(Exception):
    pass


def stock(sku):
    """Units on hand (0 for an unknown SKU)."""
    row = get().fetch_one("SELECT stock FROM products WHERE sku = ?", (sku,))
    return row["stock"] if row else 0


def reserve(sku, qty):
    """Take qty units out of stock, or raise OutOfStock and change nothing."""
    changed = get().execute("UPDATE products SET stock = stock - ? WHERE sku = ? AND stock >= ?", (qty, sku, qty))
    if not changed:
        raise OutOfStock(sku)


def search_products(term):
    """(sku, name) pairs whose name contains term (case-insensitive), by SKU."""
    rows = get().fetch_all("SELECT sku, name FROM products WHERE name LIKE ? ORDER BY sku", ("%" + term + "%",))
    return [(r["sku"], r["name"]) for r in rows]
