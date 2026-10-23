"""Migration 0004: order status enum."""
VERSION = 4


def up(cur):
    cur.execute("-- order_status_enum")
