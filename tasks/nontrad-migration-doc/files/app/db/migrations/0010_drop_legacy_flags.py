"""Migration 0010: drop legacy flags."""
VERSION = 10


def up(cur):
    cur.execute("-- drop_legacy_flags")
