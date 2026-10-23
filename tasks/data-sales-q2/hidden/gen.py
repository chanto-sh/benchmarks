"""Generates files/orders.csv and files/fx.csv (run once; the output is committed)."""
import csv
import random
import sys
from pathlib import Path

out = Path(sys.argv[1])
rng = random.Random(4242)
regions = ["north", "south", "east", "west", "central"]
skus = {"A-100": 19.99, "A-200": 34.50, "B-310": 7.25, "C-005": 120.00, "C-777": 64.90, "D-042": 2.75}
fx = {}
for m in range(1, 10):
    fx[(m, "EUR")] = round(1.05 + 0.01 * m + rng.random() * 0.02, 4)
    fx[(m, "GBP")] = round(1.24 + 0.005 * m + rng.random() * 0.02, 4)
with open(out / "fx.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["month", "currency", "usd_per_unit"])
    for (m, c), v in sorted(fx.items()):
        w.writerow([f"2026-{m:02}", c, v])

rows = []
for i in range(1, 2401):
    m = rng.randint(1, 9)
    d = rng.randint(1, 28)
    region = rng.choice(regions)
    style = rng.random()
    if style < 0.1:
        region = region.upper()
    elif style < 0.2:
        region = region.capitalize() + " "
    sku = rng.choice(list(skus))
    price = skus[sku]
    cur = rng.choices(["USD", "EUR", "GBP"], [6, 3, 1])[0]
    unit = round(price * rng.uniform(0.8, 1.0), 2)
    qty = str(rng.randint(1, 12)) if rng.random() > 0.02 else ""
    status = rng.choices(["completed", "refunded", "cancelled", "Completed"], [80, 8, 7, 5])[0]
    date = f"2026-{m:02}-{d:02}" if rng.random() > 0.15 else f"{m:02}/{d:02}/2026"
    cust = f"C{rng.randint(1, 600):04}"
    rows.append([f"O{i:05}", date, cust, region, sku, qty, f"{unit:.2f}", cur, status, f"{price:.2f}"])
# The export retried some pages: exact duplicate rows.
dups = rng.sample(rows, 90)
for r in dups:
    rows.insert(rng.randint(0, len(rows)), list(r))
with open(out / "orders.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["order_id", "order_date", "customer_id", "region", "sku", "qty", "unit_price", "currency", "status", "list_price"])
    w.writerows(rows)
