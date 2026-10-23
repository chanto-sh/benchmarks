"""Migration 0006: invoice currency."""
VERSION = 6


def up(cur):
    cur.execute("-- invoice_currency")
