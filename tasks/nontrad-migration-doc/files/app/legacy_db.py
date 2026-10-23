"""Thin wrapper over the old DB-API driver. Deprecated: use app.db.session.

Every call opens its own connection and builds SQL from strings.
"""
import os

from app import settings

TIMEOUT_S = float(os.environ.get("LEGACY_DB_TIMEOUT_S", "30"))


def _connect():
    import sqlite3  # stand-in for the real driver in this repo
    return sqlite3.connect(settings.DB_URL, timeout=TIMEOUT_S)


def query_raw(sql, *params):
    """Run SQL and return all rows. Deprecated."""
    with _connect() as conn:
        return conn.execute(sql, params).fetchall()
