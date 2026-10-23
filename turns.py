#!/usr/bin/env python3
"""Per-turn cost build-up across agents, from an existing meter log.

Each meter record is one model call: {t, label, input, output, cached}. A label
(`agent~task~rep~id`) is one session; its calls ordered by time are its turns.
So this reconstructs, per agent, how cost and tokens build up turn by turn —
the thing that separates agents over a long session (does history get re-sent
uncached, or cached?). No model is run; it only reads the log.

    python3 turns.py [meter.jsonl] [--max-turns 30] [--min-sessions 5]

Prices default to DeepSeek V4.1 Flash off-peak (the proxy's rates): input
$0.15/M, cached reads 0.1x, output $0.60/M.
"""
import argparse, json, statistics, sys
from collections import defaultdict

IN, CACHED_MULT, OUT = 0.15e-6, 0.1, 0.60e-6
SKIP = {"v1", "probe", "unlabelled", ""}


def call_cost(inp, cached, out):
    uncached = max(0, inp - cached)
    return uncached * IN + cached * IN * CACHED_MULT + out * OUT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", nargs="?", default="meter.jsonl")
    ap.add_argument("--max-turns", type=int, default=30)
    ap.add_argument("--min-sessions", type=int, default=5)
    a = ap.parse_args()

    sessions = defaultdict(list)  # label -> [(t, input, output, cached)]
    for line in open(a.log):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        lab = d.get("label", "")
        agent = lab.split("~")[0]
        if agent in SKIP or d.get("status") != 200:
            continue
        sessions[lab].append((d["t"], d.get("input", 0), d.get("output", 0), d.get("cached", 0)))

    # agent -> list of sessions, each a list of per-turn dicts (cumulative cost/tokens)
    agents = defaultdict(list)
    for lab, calls in sessions.items():
        calls.sort()
        agent = lab.split("~")[0]
        turns, cc, cu = [], 0.0, 0
        for (_, inp, out, cached) in calls:
            cc += call_cost(inp, cached, out)
            cu += max(0, inp - cached)
            turns.append({"in": inp, "cached": cached, "cum_cost": cc, "cum_uncached": cu})
        agents[agent].append(turns)

    # Summary table
    rows = []
    for agent, sess in agents.items():
        lens = [len(s) for s in sess]
        tot_in = sum(t["in"] for s in sess for t in s)
        tot_cached = sum(t["cached"] for s in sess for t in s)
        hit = tot_cached / tot_in if tot_in else 0.0
        rows.append((agent, len(sess), statistics.median(lens), max(lens), hit))
    rows.sort(key=lambda r: -r[4])  # by cache-hit rate
    print(f"{'agent':16} {'sessions':>8} {'med turns':>9} {'max':>5} {'cache-hit%':>10}")
    for agent, n, med, mx, hit in rows:
        print(f"{agent:16} {n:8d} {med:9.0f} {mx:5d} {hit*100:9.1f}%")

    # Cumulative cost vs turn, per agent (median across that agent's sessions)
    print(f"\nMedian cumulative cost ($) by turn (agents with >= {a.min_sessions} sessions reaching the turn):")
    marks = [t for t in (5, 10, 15, 20, 25, 30) if t <= a.max_turns]
    hdr = "agent".ljust(16) + "".join(f"turn{t:>3}".rjust(10) for t in marks)
    print(hdr)
    curve = {}
    for agent, sess in agents.items():
        line = agent.ljust(16)
        row = {}
        for t in marks:
            vals = [s[t - 1]["cum_cost"] for s in sess if len(s) >= t]
            if len(vals) >= a.min_sessions:
                m = statistics.median(vals)
                row[t] = m
                line += f"${m:8.4f}".rjust(10)
            else:
                line += f"{'-':>10}"
        curve[agent] = row
        print(line)

    # Headline: at the deepest common turn, who is cheapest vs priciest
    deep = max((t for t in marks if sum(1 for a2 in curve if t in curve[a2]) >= 3), default=None)
    if deep:
        ranked = sorted(((v[deep], ag) for ag, v in curve.items() if deep in v))
        print(f"\nAt turn {deep}, median cumulative cost: "
              f"cheapest {ranked[0][1]} ${ranked[0][0]:.4f} -> priciest {ranked[-1][1]} ${ranked[-1][0]:.4f} "
              f"({ranked[-1][0]/ranked[0][0]:.1f}x)")


if __name__ == "__main__":
    main()
