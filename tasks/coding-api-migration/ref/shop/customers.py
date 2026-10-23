from .db import get


def find_customer(email):
    """The customer with this email (case-insensitive) as a dict, or None."""
    return get().fetch_one("SELECT id, name, email, tier FROM customers WHERE lower(email) = lower(?)", (email,))


def customers_by_tier(tier):
    """Names of customers in a tier, alphabetically."""
    return [r["name"] for r in get().fetch_all("SELECT name FROM customers WHERE tier = ? ORDER BY name", (tier,))]


def add_customer(name, email, tier="basic"):
    db = get()
    db.execute("INSERT INTO customers (name, email, tier) VALUES (?, ?, ?)", (name, email, tier))
    return db.fetch_one("SELECT last_insert_rowid() AS id")["id"]
