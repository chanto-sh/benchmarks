"""Migration 0002: add customers."""
VERSION = 2


def up(cur):
    cur.execute("-- add_customers")
