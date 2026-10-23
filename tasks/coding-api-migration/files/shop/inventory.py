from .db import query


class OutOfStock(Exception):
    pass


def stock(sku):
    """Units on hand (0 for an unknown SKU)."""
    rows = query("SELECT stock FROM products WHERE sku = %s", sku)
    return rows[0][0] if rows else 0


def reserve(sku, qty):
    """Take qty units out of stock, or raise OutOfStock and change nothing."""
    if stock(sku) < qty:
        raise OutOfStock(sku)
    query("UPDATE products SET stock = stock - %s WHERE sku = %s", qty, sku)


def search_products(term):
    """(sku, name) pairs whose name contains term (case-insensitive), by SKU."""
    return query("SELECT sku, name FROM products WHERE name LIKE %s ORDER BY sku", "%" + term + "%")
