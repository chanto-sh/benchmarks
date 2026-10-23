"""Database access for the shop.

Use `get()` for the current `Database` and its fetch_all / fetch_one / execute
methods (qmark `?` placeholders, rows come back as dicts).
"""
import sqlite3
import warnings

_db = None


class Database:
    def __init__(self, conn):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    def fetch_all(self, sql, params=()):
        """All rows as a list of dicts."""
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def fetch_one(self, sql, params=()):
        """The first row as a dict, or None."""
        r = self.conn.execute(sql, params).fetchone()
        return dict(r) if r is not None else None

    def execute(self, sql, params=()):
        """Run a write statement, commit, and return the number of rows changed."""
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.rowcount

    def executescript(self, sql):
        self.conn.executescript(sql)
        self.conn.commit()


def connect(path=":memory:"):
    """Open the database and make it the current one."""
    global _db
    _db = Database(sqlite3.connect(path, check_same_thread=False))
    return _db


def get():
    if _db is None:
        raise RuntimeError("shop.db.connect() has not been called")
    return _db


def query(sql, *args):
    """DEPRECATED (removed in shop 3.0): use get().fetch_all/fetch_one/execute.

    Legacy helper: `%s` placeholders, positional args, returns a list of tuples
    (an empty list for statements that return no rows) and commits after every call.
    """
    warnings.warn("shop.db.query() is deprecated; use shop.db.get()", DeprecationWarning, stacklevel=2)
    db = get()
    cur = db.conn.execute(sql.replace("%s", "?"), args)
    rows = [tuple(r) for r in cur.fetchall()]
    db.conn.commit()
    return rows
