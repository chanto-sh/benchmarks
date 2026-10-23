"""Migration 0005: add invoices."""
VERSION = 5


def up(cur):
    cur.execute("-- add_invoices")
