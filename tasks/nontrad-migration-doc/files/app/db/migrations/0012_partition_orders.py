"""Migration 0012: partition orders."""
VERSION = 12


def up(cur):
    cur.execute("-- partition_orders")
