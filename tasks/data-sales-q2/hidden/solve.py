"""Reference answers computed from the pristine data."""
import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def solve(d):
    d = Path(d)
    fx = {(r["month"], r["currency"]): Decimal(r["usd_per_unit"]) for r in csv.DictReader(open(d / "fx.csv"))}
    raw = list(csv.reader(open(d / "orders.csv")))
    header, body = raw[0], raw[1:]
    seen, rows = set(), []
    for r in body:
        t = tuple(r)
        if t not in seen:
            seen.add(t)
            rows.append(dict(zip(header, r)))
    total = Decimal(0)
    custs = {}
    for r in rows:
        if r["status"].strip().lower() != "completed" or not r["qty"].strip():
            continue
        dt = r["order_date"]
        if "/" in dt:
            mm, dd, yy = dt.split("/")
            dt = f"{yy}-{mm}-{dd}"
        month = dt[:7]
        region = r["region"].strip().lower()
        custs.setdefault(region, set()).add(r["customer_id"])
        if month in ("2026-04", "2026-05", "2026-06"):
            amt = int(r["qty"]) * Decimal(r["unit_price"])
            if r["currency"] != "USD":
                amt *= fx[(month, r["currency"])]
            total += amt
    top = max(custs, key=lambda k: len(custs[k]))
    counts = sorted((len(v) for v in custs.values()), reverse=True)
    assert counts[0] != counts[1], "tie"
    return {
        "q2_revenue_usd": float(total.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        "top_region_by_customers": top,
        "duplicate_rows_removed": len(body) - len(rows),
        "q2_gross_margin_pct": "not in data",
    }


if __name__ == "__main__":
    import json, sys
    print(json.dumps(solve(sys.argv[1]), indent=2))
