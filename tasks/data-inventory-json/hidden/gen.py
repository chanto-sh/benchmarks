"""Generates files/inventory.json (run once; output is committed)."""
import json
import random
import sys
from pathlib import Path

out = Path(sys.argv[1])
rng = random.Random(55)
families = ["BX", "CR", "PL", "TB"]
catalog = {}
for fam in families:
    for n in range(1, 61):
        kg = round(rng.uniform(0.05, 25.0), 3)
        catalog[f"{fam}-{n:03}"] = (kg, round(rng.uniform(1.5, 300.0), 2))
whs = []
for code, active in [("AMS1", True), ("RTM2", True), ("LEJ1", True), ("PRG0", False), ("WAW3", True)]:
    items = []
    for sku in rng.sample(list(catalog), 140):
        kg, cost = catalog[sku]
        unit = rng.choice(["g", "kg", "lb"])
        val = {"g": kg * 1000, "kg": kg, "lb": kg / 0.45359237}[unit]
        shown = sku if rng.random() > 0.15 else rng.choice([sku.lower(), f" {sku}", f"{sku} "])
        bins = 2 if rng.random() < 0.1 else 1
        for _ in range(bins):
            items.append({
                "sku": shown,
                "bin": f"{rng.choice('ABCDEFG')}{rng.randint(1, 40):02}",
                "qty": rng.randint(0, 250 if active else 420),
                "unit_weight": {"value": round(val, 4), "unit": unit},
                "weight_est_kg": round(kg * rng.uniform(0.7, 1.4), 1),
                "unit_cost_usd": cost,
            })
    whs.append({"code": code, "active": active, "items": items})
json.dump({"generated": "2026-10-01", "warehouses": whs}, open(out / "inventory.json", "w"), indent=1)
