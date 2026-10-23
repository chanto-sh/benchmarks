from .db import query


def revenue_by_tier():
    """[(tier, cents)] for tiers with orders, highest revenue first (ties by tier)."""
    return query("""
        SELECT c.tier, SUM(l.qty * l.price_cents)
        FROM order_lines l JOIN orders o ON o.id = l.order_id JOIN customers c ON c.id = o.customer_id
        GROUP BY c.tier ORDER BY 2 DESC, 1
    """)


def best_sellers(n=3):
    """[(sku, units)] most units sold first (ties by sku)."""
    return query("SELECT sku, SUM(qty) FROM order_lines GROUP BY sku ORDER BY 2 DESC, 1 LIMIT %s", n)
