from app import legacy_db
from app.util.env import env

CURRENCY = env("BILLING_CURRENCY", "EUR")


def unpaid(customer_id):
    rows = legacy_db.query_raw("SELECT id, amount FROM invoices WHERE customer_id = ? AND paid = 0", customer_id)
    return [(i, a, CURRENCY) for i, a in rows]
