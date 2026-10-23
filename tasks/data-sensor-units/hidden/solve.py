"""Reference answers computed from the pristine data."""
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def to_c(v, u):
    return v if u == "C" else (v - 32) * 5 / 9 if u == "F" else v - 273.15


def r2(x):
    return float(Decimal(repr(x)).quantize(Decimal("0.01"), ROUND_HALF_UP))


def solve(d):
    d = Path(d)
    sensors = {s["id"]: s for s in json.load(open(d / "sensors.json"))}
    readings = json.load(open(d / "readings.json"))["readings"]
    invalid = 0
    day = {}
    hottest = (None, -1e9)
    for r in readings:
        v = r["value"]
        if v is None or v == -999:
            invalid += 1
            continue
        s = sensors[r["sensor"]]
        c = to_c(v, r.get("unit", s["default_unit"]))
        ts = datetime.fromisoformat(r["ts"]).astimezone(timezone.utc)
        if ts.date().isoformat() == "2026-08-14":
            day.setdefault(s["site"], []).append(c)
        if c > hottest[1]:
            hottest = (s["site"], c)
    return {
        "site_mean_c_2026_08_14": {k: r2(sum(v) / len(v)) for k, v in sorted(day.items())},
        "hottest_site": hottest[0],
        "invalid_readings": invalid,
        "mean_humidity_pct": "not in data",
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(solve(sys.argv[1]), indent=2))
