"""JSON export of the ledger."""
import json

from .common import fmt_money, in_range, load_rows, parse_ts


def export(path, start=None, end=None):
    rows = [r for r in load_rows(path) if in_range(r, start, end)]
    doc = {
        "rows": [{"ts": parse_ts(r["ts"]).isoformat(), "account": r["account"], "amount": fmt_money(r["cents"])}
                 for r in rows],
        "total": fmt_money(sum(r["cents"] for r in rows)),
    }
    return json.dumps(doc, indent=2)
