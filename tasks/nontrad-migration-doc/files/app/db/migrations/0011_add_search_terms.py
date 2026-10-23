"""Migration 0011: add search terms."""
VERSION = 11


def up(cur):
    cur.execute("-- add_search_terms")
