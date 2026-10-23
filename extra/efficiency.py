#!/usr/bin/env python3
"""Tool-loop efficiency from benchmark result JSONs.

    python3 extra/efficiency.py results/*.json

Cells are (agent, task, rep). When the same cell appears in several files the
newest file wins, so a shard that was re-run after a crash replaces its partial
predecessor. Prints a markdown table plus head-to-head pair counts against the
agent named by --baseline (default: chanto).
"""

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def load(paths):
    newest = {}
    for p in sorted(paths, key=lambda p: p.stat().st_mtime):
        data = json.loads(p.read_text())
        for r in data.get("results", []):
            key = (r["agent"], r["task"], r.get("rep", 0))
            newest[key] = r
    return list(newest.values())


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else 0


def med_s(xs):
    """A median, or `n/a` when the agent reports no such number."""
    xs = [x for x in xs if x is not None]
    return f"{statistics.median(xs):,.0f}" if xs else "n/a"


def tokens_in(r):
    """Input tokens, from the usage block when present, else the token tally."""
    usage = r.get("usage")
    if usage:
        return usage.get("input")
    return (r.get("tokens") or {}).get("in")


def tokens_out(r):
    usage = r.get("usage")
    if usage:
        return usage.get("output")
    return (r.get("tokens") or {}).get("out")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--baseline", default="chanto")
    args = ap.parse_args()

    rows = load(args.files)
    if not rows:
        raise SystemExit("no results")
    by = defaultdict(list)
    for r in rows:
        by[r["agent"]].append(r)
    tasks = len({r["task"] for r in rows})
    print(f"{len(rows)} cells over {tasks} tasks\n")
    print("| agent | solved | 95% CI | false \"done\" | timeouts | median calls | median calls (solved) | median in tok | median out tok | cache hit | median time |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    unmeasured = []
    for a in sorted(by, key=lambda a: -sum(r["passed"] for r in by[a]) / len(by[a])):
        rs = by[a]
        k, n = sum(r["passed"] for r in rs), len(rs)
        lo, hi = wilson(k, n)
        solved = [r for r in rs if r["passed"]]
        calls = [r.get("usage", {}).get("requests") for r in rs if r.get("usage")]
        calls_solved = [r.get("usage", {}).get("requests") for r in solved if r.get("usage")]
        ins = [t for r in rs if (t := tokens_in(r)) is not None]
        outs = [t for r in rs if (t := tokens_out(r)) is not None]
        cached = sum(r["usage"].get("cached", 0) for r in rs if r.get("usage"))
        total_in = sum(ins)
        hit = f"{100 * cached / total_in:.0f}%" if total_in else "n/a"
        # `claimed_done` is only meaningful where the agent prints a structured
        # completion signal; for the rest a false "done" is unmeasurable, not zero.
        known = [r for r in rs if r.get("claimed_done") is not None]
        fd = sum(bool(r.get("false_done")) for r in known)
        fd_s = f"{fd} of {len(known)}" if known else "n/a"
        if not known:
            unmeasured.append(a)
        to = sum(bool(r.get("timed_out")) for r in rs)
        print(
            f"| {a} | {k}/{n} ({100 * k / n:.0f}%) | {100 * lo:.0f}–{100 * hi:.0f}% | {fd_s} | {to} | "
            f"{med_s(calls)} | {med_s(calls_solved)} | {med_s(ins)} | {med_s(outs)} | {hit} | "
            f"{med([r['seconds'] for r in rs]):.0f}s |"
        )

    if unmeasured:
        print(f"\n`n/a`: {', '.join('`' + a + '`' for a in unmeasured)} print no "
              f"structured completion signal, so a false \"done\" is unmeasurable "
              f"(shown as zero before).")

    base = args.baseline
    if base not in by:
        return
    print(f"\n## Paired head-to-head against `{base}` (same task and rep)\n")
    bmap = {(r["task"], r.get("rep", 0)): r for r in by[base]}
    print("| agent | pairs | only baseline | only agent | both | neither | p (sign test) |")
    print("|---|---|---|---|---|---|---|")
    for a in sorted(by):
        if a == base:
            continue
        amap = {(r["task"], r.get("rep", 0)): r for r in by[a]}
        common = bmap.keys() & amap.keys()
        only_b = sum(bmap[k]["passed"] and not amap[k]["passed"] for k in common)
        only_a = sum(amap[k]["passed"] and not bmap[k]["passed"] for k in common)
        both = sum(bmap[k]["passed"] and amap[k]["passed"] for k in common)
        neither = sum(not bmap[k]["passed"] and not amap[k]["passed"] for k in common)
        # Two-sided exact binomial over the discordant pairs only.
        d = only_b + only_a
        p = min(1.0, 2 * sum(math.comb(d, i) for i in range(min(only_b, only_a) + 1)) / 2**d) if d else 1.0
        print(f"| {a} | {len(common)} | {only_b} | {only_a} | {both} | {neither} | {p:.2f} |")


if __name__ == "__main__":
    main()
