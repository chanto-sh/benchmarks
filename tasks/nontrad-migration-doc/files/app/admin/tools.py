from app.legacy_db import query_raw as qr


def purge_test_customers():
    return qr("DELETE FROM customers WHERE email LIKE '%@example.test'")
