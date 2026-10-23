"""Generates files/sensors.json and files/readings.json (run once; output is committed)."""
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

out = Path(sys.argv[1])
rng = random.Random(777)
sites = {"harbor": 14.0, "ridge": 6.0, "mill": 19.0, "quarry": 22.5}
sensors = []
units = ["C", "F", "K"]
for i in range(1, 25):
    site = list(sites)[i % 4]
    sensors.append({"id": f"S{i:03}", "site": site, "default_unit": units[i % 3], "humidity_capable": i % 5 == 0})


def conv(c, u):
    return c if u == "C" else c * 9 / 5 + 32 if u == "F" else c + 273.15


offsets = [timezone.utc, timezone(timedelta(hours=-2)), timezone(timedelta(hours=5, minutes=30)), timezone(timedelta(hours=9))]
readings = []
start = datetime(2026, 8, 12, tzinfo=timezone.utc)
for n in range(3000):
    s = rng.choice(sensors)
    t = start + timedelta(minutes=rng.randint(0, 4 * 24 * 60 - 1))
    tz = rng.choice(offsets)
    c = sites[s["site"]] + rng.gauss(0, 3)
    unit = s["default_unit"] if rng.random() < 0.3 else rng.choice(units)
    v = round(conv(c, unit), 2)
    r = {"sensor": s["id"], "ts": t.astimezone(tz).isoformat(), "value": v}
    if unit != s["default_unit"] or rng.random() < 0.5:
        r["unit"] = unit
    x = rng.random()
    if x < 0.02:
        r["value"] = None
    elif x < 0.035:
        r["value"] = -999
    readings.append(r)
# A heat spike at ridge in Celsius, and a warm Kelvin reading (no unit field:
# the sensor default applies) that only looks largest if units are ignored.
readings.insert(1200, {"sensor": "S001", "ts": "2026-08-13T12:00:00+09:00", "value": 41.2, "unit": "C"})
readings.insert(2100, {"sensor": "S011", "ts": "2026-08-14T10:00:00+00:00", "value": 310.0})
json.dump(sensors, open(out / "sensors.json", "w"), indent=1)
json.dump({"exported_at": "2026-08-16T06:00:00Z", "readings": readings}, open(out / "readings.json", "w"), indent=1)
