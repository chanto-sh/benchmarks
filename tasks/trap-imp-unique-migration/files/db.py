"""Tiny migration runner for the accounts service (SQLite)."""
import sqlite3
from pathlib import Path

MIGRATIONS = Path(__file__).parent / "migrations"


def connect(path=":memory:"):
    return sqlite3.connect(path)


def apply(conn, name):
    """Run one migration file, e.g. apply(conn, "001_users.sql")."""
    conn.executescript((MIGRATIONS / name).read_text())


def migrate(conn):
    for p in sorted(MIGRATIONS.glob("*.sql")):
        apply(conn, p.name)
