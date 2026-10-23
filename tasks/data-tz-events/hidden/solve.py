"""Reference answers computed from the pristine data."""
import csv
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def solve(d):
    d = Path(d)
    tz = {r["user_id"]: ZoneInfo(r["timezone"]) for r in csv.DictReader(open(d / "users.csv"))}
    sat = 0
    hours = [0] * 24
    berlin = 0
    for r in csv.DictReader(open(d / "events.csv")):
        utc = datetime.fromisoformat(r["occurred_at"].replace("Z", "+00:00"))
        local = utc.astimezone(tz[r["user_id"]])
        if local.weekday() == 5:
            sat += 1
        if r["event_type"].strip().lower() == "purchase":
            hours[local.hour] += 1
            if str(tz[r["user_id"]]) == "Europe/Berlin" and local.date().isoformat() == "2026-03-29":
                berlin += 1
    top = max(range(24), key=lambda h: hours[h])
    assert sorted(hours)[-1] != sorted(hours)[-2], "tie"
    return {"saturday_local_events": sat, "busiest_local_purchase_hour": top, "berlin_purchases_2026_03_29": berlin}


if __name__ == "__main__":
    import sys
    print(json.dumps(solve(sys.argv[1]), indent=2))
