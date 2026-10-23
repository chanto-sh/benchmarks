"""Reference answers computed from the pristine data."""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

TO_KG = {"g": Decimal("0.001"), "kg": Decimal(1), "lb": Decimal("0.45359237")}


def solve(d):
    data = json.load(open(Path(d) / "inventory.json"))
    bx = Decimal(0)
    skus = set()
    value = {}
    for w in data["warehouses"]:
        if not w["active"]:
            continue
        v = Decimal(0)
        for it in w["items"]:
            sku = it["sku"].strip().upper()
            skus.add(sku)
            kg = Decimal(str(it["unit_weight"]["value"])) * TO_KG[it["unit_weight"]["unit"]]
            if sku.startswith("BX-"):
                bx += kg * it["qty"]
            v += Decimal(str(it["unit_cost_usd"])) * it["qty"]
        value[w["code"]] = v
    best = sorted(value.items(), key=lambda kv: -kv[1])
    assert best[0][1] != best[1][1]
    return {
        "bx_total_weight_kg": float(bx.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        "distinct_skus": len(skus),
        "highest_value_warehouse": best[0][0],
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(solve(sys.argv[1]), indent=2))
