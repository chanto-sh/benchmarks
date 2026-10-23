"""Reference answers: rebuild the database privately and compute in plain Python."""
import json
import sqlite3
import sys
import tempfile
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gen import build  # noqa: E402


def solve(_files=None):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "library.db"
        build(p)
        db = sqlite3.connect(p)
        period = int(db.execute("SELECT value FROM settings WHERE key='loan_period_days'").fetchone()[0])
        genre = dict(db.execute("SELECT id, genre FROM books"))
        names = dict(db.execute("SELECT id, name FROM members"))
        loans = db.execute("SELECT book_id, member_id, loaned_on, returned_on FROM loans").fetchall()
        db.close()
    asof = date(2026, 9, 30)
    overdue, late, hist = 0, {}, []
    for b, m, lo, ro in loans:
        lo = date.fromisoformat(lo)
        ro = date.fromisoformat(ro) if ro else None
        due = lo + timedelta(days=period)
        if lo <= asof and (ro is None or ro > asof) and due < asof:
            overdue += 1
        if ro and ro > due:
            late[m] = late.get(m, 0) + 1
        if ro and genre[b].strip().lower() == "history":
            hist.append((ro - lo).days)
    top = sorted(late.items(), key=lambda kv: -kv[1])
    assert top[0][1] > top[1][1], "tie"
    avg = Decimal(sum(hist)) / Decimal(len(hist))
    return {
        "overdue_as_of_2026_09_30": overdue,
        "member_most_late_returns": names[top[0][0]],
        "avg_history_loan_days": float(avg.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        "loans_in_2024": "not in data",
    }


if __name__ == "__main__":
    print(json.dumps(solve(), indent=2))
