from .db import query


def find_customer(email):
    """The customer with this email (case-insensitive) as a dict, or None."""
    rows = query("SELECT id, name, email, tier FROM customers WHERE lower(email) = lower(%s)", email)
    if not rows:
        return None
    r = rows[0]
    return {"id": r[0], "name": r[1], "email": r[2], "tier": r[3]}


def customers_by_tier(tier):
    """Names of customers in a tier, alphabetically."""
    return [r[0] for r in query("SELECT name FROM customers WHERE tier = %s ORDER BY name", tier)]


def add_customer(name, email, tier="basic"):
    query("INSERT INTO customers (name, email, tier) VALUES (%s, %s, %s)", name, email, tier)
    return query("SELECT last_insert_rowid()")[0][0]
