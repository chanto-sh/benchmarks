"""Migration 0001: init."""
VERSION = 1


def up(cur):
    cur.execute("-- init")
