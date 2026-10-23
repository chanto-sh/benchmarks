"""Resolve production dependencies of an app against registry.json.

Workspace packages ("workspace:*") are followed through their "dependencies"
(devDependencies are never followed). For every external package the highest
registry version satisfying all collected constraints wins; constraints from
external packages come from the version currently chosen, so we iterate to a
fixed point.

Range syntax: "1.2.3" exact, "^1.2.3", "~1.2.3", or space-separated
comparators like ">=1.2.0 <1.5.0".
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def ver(s):
    return tuple(int(x) for x in s.split("."))


def satisfies(v, rng):
    v = ver(v)
    for part in rng.split():
        if part.startswith("^"):
            b = ver(part[1:])
            if not (b <= v < (b[0] + 1, 0, 0)):
                return False
        elif part.startswith("~"):
            b = ver(part[1:])
            if not (b <= v < (b[0], b[1] + 1, 0)):
                return False
        elif part.startswith(">="):
            if v < ver(part[2:]):
                return False
        elif part.startswith("<"):
            if v >= ver(part[1:]):
                return False
        elif v != ver(part):
            return False
    return True


def workspace():
    out = {}
    for m in ROOT.glob("*/*/manifest.json"):
        data = json.loads(m.read_text())
        out[data["name"]] = data
    return out


def resolve(app):
    ws = workspace()
    registry = json.loads((ROOT / "registry.json").read_text())
    direct = []  # (package, range) from workspace prod deps reachable from the app
    seen, todo = set(), [app]
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        for dep, rng in ws[name].get("dependencies", {}).items():
            if rng.startswith("workspace:"):
                todo.append(dep)
            else:
                direct.append((dep, rng))
    chosen = {}
    for _ in range(20):
        cons = {}
        for dep, rng in direct:
            cons.setdefault(dep, []).append(rng)
        for pkg, v in chosen.items():
            for dep, rng in registry[pkg][v].get("dependencies", {}).items():
                cons.setdefault(dep, []).append(rng)
        new = {}
        for pkg, ranges in cons.items():
            ok = [v for v in registry[pkg] if all(satisfies(v, r) for r in ranges)]
            if not ok:
                raise SystemExit(f"no version of {pkg} satisfies {ranges}")
            new[pkg] = max(ok, key=ver)
        if new == chosen:
            return chosen
        chosen = new
    raise SystemExit("did not converge")


if __name__ == "__main__":
    for pkg, v in sorted(resolve(sys.argv[1] if len(sys.argv) > 1 else "@acme/web").items()):
        print(f"{pkg} {v}")
