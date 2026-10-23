import sqlite3
import unittest
from pathlib import Path

import db


class MigrationTests(unittest.TestCase):
    def test_constraint_on_fresh_db(self):
        conn = db.connect()
        db.migrate(conn)
        conn.execute("INSERT INTO users (email, name) VALUES ('kim@example.com', 'Kim')")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO users (email, name) VALUES ('KIM@example.com', 'Kim 2')")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO users (email, name) VALUES (NULL, 'Nobody')")

    def test_applies_to_prod_snapshot(self):
        conn = db.connect()
        db.apply(conn, "001_users.sql")
        conn.executescript(Path("fixtures/prod_snapshot.sql").read_text())
        before = conn.execute("SELECT id, email, name FROM users ORDER BY id").fetchall()
        db.apply(conn, "002_unique_email.sql")
        after = conn.execute("SELECT id, email, name FROM users ORDER BY id").fetchall()
        self.assertEqual(before, after, "the migration must not change customer rows")


if __name__ == "__main__":
    unittest.main()
