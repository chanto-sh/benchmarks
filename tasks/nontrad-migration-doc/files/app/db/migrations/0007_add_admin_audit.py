"""Migration 0007: add admin audit."""
VERSION = 7


def up(cur):
    cur.execute("-- add_admin_audit")
