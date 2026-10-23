"""Summarise sales exports: total units and revenue per SKU across stores.

Usage: summarize.py data/a.csv [data/b.csv ...]  (JSON on stdout)
"""
import csv
import json
import sys
from decimal import Decimal


def main(paths):
    skus = {}
    for path in paths:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                qty = int(row["qty"])
                price = Decimal(row["unit_price"])
                s = skus.setdefault(row["sku"], {"units": 0, "revenue": Decimal("0")})
                # Stream as we go (exports can be large); a bad row aborts mid-file.
                s["units"] += qty
                s["revenue"] += qty * price
    out = {k: {"units": v["units"], "revenue": str(v["revenue"].quantize(Decimal("0.01")))}
           for k, v in sorted(skus.items())}
    json.dump({"files": len(paths), "skus": out}, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
