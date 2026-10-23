"""Builds library.db in the given directory (setup.sh runs this in the workspace)."""
import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path


def build(path):
    path = Path(path)
    if path.exists():
        path.unlink()
    rng = random.Random(9001)
    db = sqlite3.connect(path)
    db.executescript("""
    CREATE TABLE members(id INTEGER PRIMARY KEY, name TEXT, joined TEXT);
    CREATE TABLE books(id INTEGER PRIMARY KEY, title TEXT, genre TEXT, pages INTEGER);
    CREATE TABLE loans(id INTEGER PRIMARY KEY, book_id INTEGER, member_id INTEGER, loaned_on TEXT, returned_on TEXT);
    CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
    """)
    first = ["Ada", "Bo", "Cyd", "Dee", "Eli", "Fay", "Gus", "Hal", "Ivy", "Jo", "Kit", "Lu", "Max", "Nia", "Oz", "Pip"]
    last = ["Marsh", "Okafor", "Lind", "Sato", "Reyes", "Quill", "Brandt", "Haas", "Ng", "Vale"]
    names = rng.sample([f"{a} {b}" for a in first for b in last], 140)
    for i, n in enumerate(names, 1):
        db.execute("INSERT INTO members VALUES(?,?,?)", (i, n, str(date(2025, 3, 1) + timedelta(days=rng.randint(0, 400)))))
    genres = ["History", "history ", "HISTORY", "Fiction", "fiction", "Science", "Poetry", "Travel"]
    for i in range(1, 501):
        db.execute("INSERT INTO books VALUES(?,?,?,?)", (i, f"Title {i:03}", rng.choice(genres), rng.randint(80, 900)))
    loan_id = 0
    for _ in range(4200):
        loan_id += 1
        m = rng.randint(1, 140)
        # A few members are chronically late.
        late_bias = 0.6 if m in (17, 88) else 0.15
        start = date(2025, 3, 1) + timedelta(days=rng.randint(0, 588))
        if rng.random() < late_bias:
            dur = rng.randint(22, 70)
        else:
            dur = rng.randint(1, 21)
        ret = start + timedelta(days=dur)
        returned = None if ret > date(2026, 10, 10) or rng.random() < 0.03 else str(ret)
        db.execute("INSERT INTO loans VALUES(?,?,?,?,?)", (loan_id, rng.randint(1, 500), m, str(start), returned))
    db.execute("INSERT INTO settings VALUES('loan_period_days','21')")
    db.execute("INSERT INTO settings VALUES('max_renewals','2')")
    db.execute("INSERT INTO meta VALUES('migrated_on','2025-03-01')")
    db.execute("INSERT INTO meta VALUES('migration_note','Only loans opened on or after migrated_on were imported from the old catalogue; earlier history was not migrated.')")
    db.commit()
    db.close()


if __name__ == "__main__":
    build(Path(sys.argv[1]) / "library.db")
