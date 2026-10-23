"""Migration 0014: add refunds."""
VERSION = 14


def up(cur):
    cur.execute("-- add_refunds")
