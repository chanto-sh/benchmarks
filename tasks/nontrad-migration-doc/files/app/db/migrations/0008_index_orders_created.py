"""Migration 0008: index orders created."""
VERSION = 8


def up(cur):
    cur.execute("-- index_orders_created")
