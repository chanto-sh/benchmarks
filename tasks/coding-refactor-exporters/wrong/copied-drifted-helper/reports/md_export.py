"""Markdown export of the ledger (for the monthly email)."""

from .common import fmt_money, in_range, load_rows, parse_ts


def export(path, start=None, end=None):
    rows = [r for r in load_rows(path) if in_range(r, start, end)]
    out = ["| date | account | amount |", "|---|---|---:|"]
    for r in rows:
        out.append(f"| {parse_ts(r['ts']).date().isoformat()} | {r['account']} | {fmt_money(r['cents'])} |")
    out.append(f"| | **total** | **{fmt_money(sum(r['cents'] for r in rows))}** |")
    return "\n".join(out) + "\n"
