"""Migration 0003: add orders."""
VERSION = 3


def up(cur):
    cur.execute("-- add_orders")
