"""JSON export of the ledger."""
import json
from datetime import datetime, timezone


def _load_rows(path):
    """Ledger rows from a JSON-lines file; blank lines and # comments are skipped."""
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append(json.loads(line))
    return rows


def _parse_ts(s):
    """ISO date or datetime -> aware UTC datetime (naive values are taken as UTC)."""
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    if len(s) == 10:
        dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _in_range(row, start, end):
    """start <= ts < end; either bound may be None."""
    ts = _parse_ts(row["ts"])
    return (start is None or ts >= start) and (end is None or ts <= end)


def _fmt_money(cents):
    """Integer cents -> '1,234.56' (with a leading '-' when negative)."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100:,}.{cents % 100:02d}"


def export(path, start=None, end=None):
    rows = [r for r in _load_rows(path) if _in_range(r, start, end)]
    doc = {
        "rows": [{"ts": _parse_ts(r["ts"]).isoformat(), "account": r["account"], "amount": _fmt_money(r["cents"])}
                 for r in rows],
        "total": _fmt_money(sum(r["cents"] for r in rows)),
    }
    return json.dumps(doc, indent=2)
