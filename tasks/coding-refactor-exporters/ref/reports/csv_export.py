"""CSV export of the ledger."""
import csv
import io
import json

from .common import fmt_money, in_range, load_rows, parse_ts


def export(path, start=None, end=None):
    rows = [r for r in load_rows(path) if in_range(r, start, end)]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["ts", "account", "amount"])
    for r in rows:
        w.writerow([parse_ts(r["ts"]).isoformat(), r["account"], fmt_money(r["cents"])])
    w.writerow(["", "TOTAL", fmt_money(sum(r["cents"] for r in rows))])
    return buf.getvalue()
