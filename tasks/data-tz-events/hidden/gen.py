"""Generates files/users.csv and files/events.csv (run once; output is committed)."""
import csv
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

out = Path(sys.argv[1])
rng = random.Random(31337)
zones = ["America/New_York", "Europe/Berlin", "Asia/Tokyo", "Australia/Sydney", "Asia/Kolkata", "UTC"]
users = []
for i in range(1, 301):
    users.append([f"u{i:03}", rng.choice(zones), rng.choice(["free", "pro", "team"])])
with open(out / "users.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["user_id", "timezone", "plan"])
    w.writerows(users)
types = ["page_view"] * 6 + ["purchase", "Purchase", "signup", "PURCHASE "]
start = datetime(2026, 3, 1, tzinfo=timezone.utc)
rows = []
for i in range(1, 6001):
    t = start + timedelta(seconds=rng.randint(0, 45 * 86400))
    rows.append([f"e{i:05}", rng.choice(users)[0], t.strftime("%Y-%m-%dT%H:%M:%SZ"), rng.choice(types)])
rows.sort(key=lambda r: r[2])
with open(out / "events.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["event_id", "user_id", "occurred_at", "event_type"])
    w.writerows(rows)
