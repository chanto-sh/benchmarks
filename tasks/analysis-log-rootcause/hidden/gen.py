"""Seeded generator for logs/app.log. generate() also returns the injected facts."""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

N_LINES = 50000


def generate():
    rng = random.Random(20261014)
    t = datetime(2026, 10, 14, 9, 0, 0)
    end = datetime(2026, 10, 14, 13, 0, 0)
    lines = []
    facts = {"failed": [], "baseline_502": 0}
    reload_at = datetime(2026, 10, 14, 11, 21, 7)
    deploy_at = datetime(2026, 10, 14, 11, 19, 31)
    reloaded = deployed = False
    req = 0
    limit = 1000000

    def ts():
        return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03}Z"

    def add(level, svc, msg):
        lines.append(f"{ts()} {level:<5} {svc:<9} {msg}")

    while len(lines) < N_LINES - 40:
        t += timedelta(milliseconds=rng.randint(100, 700))
        if not deployed and t >= deploy_at:
            deployed = True
            add("INFO", "deployer", "rolling out inventory v2.14.0 (3/3 pods)")
            add("WARN", "inventory", "pod inventory-7c9f restarted: liveness probe failed during rollout")
            add("INFO", "deployer", "rollout of inventory v2.14.0 complete")
        if not reloaded and t >= reload_at:
            reloaded = True
            add("INFO", "payments", "watcher: /etc/payments/limits.yaml changed, reloading")
            add("INFO", "payments", "limits reloaded: max_amount_cents=10000 currency=USD")
            facts["root_line"] = len(lines)
            limit = 10000
        x = rng.random()
        if x < 0.12:
            add("ERROR", "cache", f"redis GET session:{rng.randint(1000, 9999)}: dial tcp 10.0.3.17:6379: connection refused; falling back to origin")
            continue
        if x < 0.2:
            add("DEBUG", "inventory", f"sync batch {rng.randint(1, 99999)} ok ({rng.randint(10, 400)} skus)")
            continue
        req += 1
        rid = f"r-{req:06}"
        if x < 0.55:
            path = rng.choice(["/products", "/cart", "/search?q=lamp", "/account"])
            add("INFO", "gateway", f"req={rid} GET {path} 200 {rng.randint(5, 180)}ms")
            continue
        amount = rng.choice([rng.randint(299, 9999), rng.randint(10001, 89999)])
        add("INFO", "checkout", f"req={rid} create order amount_cents={amount}")
        if rng.random() < 0.004:
            add("WARN", "inventory", f"req={rid} reserve timed out after 3000ms")
            add("ERROR", "gateway", f"req={rid} POST /checkout 502 3011ms")
            facts["baseline_502"] += 1
            continue
        if amount > limit:
            add("WARN", "payments", f"req={rid} authorize rejected: amount_cents={amount} over limit")
            add("ERROR", "gateway", f"req={rid} POST /checkout 502 {rng.randint(40, 90)}ms")
            facts["failed"].append(rid)
            continue
        add("INFO", "payments", f"req={rid} authorized amount_cents={amount}")
        add("INFO", "gateway", f"req={rid} POST /checkout 200 {rng.randint(120, 900)}ms")
    assert t < end
    return lines, facts


if __name__ == "__main__":
    lines, _ = generate()
    out = Path(sys.argv[1]) / "logs" / "app.log"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
