"""Migration 0009: add refund reason."""
VERSION = 9


def up(cur):
    cur.execute("-- add_refund_reason")
