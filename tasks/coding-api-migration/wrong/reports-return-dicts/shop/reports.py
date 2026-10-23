from .db import get


def revenue_by_tier():
    """[(tier, cents)] for tiers with orders, highest revenue first (ties by tier)."""
    return get().fetch_all("""
        SELECT c.tier AS tier, SUM(l.qty * l.price_cents) AS cents
        FROM order_lines l JOIN orders o ON o.id = l.order_id JOIN customers c ON c.id = o.customer_id
        GROUP BY c.tier ORDER BY 2 DESC, 1
    """)


def best_sellers(n=3):
    """[(sku, units)] most units sold first (ties by sku)."""
    return get().fetch_all("SELECT sku, SUM(qty) AS units FROM order_lines GROUP BY sku ORDER BY 2 DESC, 1 LIMIT ?", (n,))
