from app.legacy_db import query_raw


def open_orders(customer_id):
    return query_raw("SELECT id, total FROM orders WHERE customer_id = ? AND status = 'open'", customer_id)


def cancel(order_id):
    query_raw("UPDATE orders SET status = 'cancelled' WHERE id = ?", order_id)
