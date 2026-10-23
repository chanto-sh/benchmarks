#!/usr/bin/env python3
"""Compare benchmark runs across models and agents.

    python3 compare.py \
        --run "DeepSeek V4 Flash=results/A.json,results/B.json" \
        --run "Qwen3.5-9B=results/C.json,results/D.json" \
        --small "Qwen3.5-9B" --strong "DeepSeek V4 Flash" [--cost "DeepSeek V4 Flash=1.20"]

Answers three questions, as markdown:
1. Same model, different agents: who solves more, and head to head on the
   same tasks (tasks Chanto solved and the other didn't, and vice versa).
2. Small model with Chanto vs strong model with the other agents.
3. Verified mode: pass rate and false "done" with and without --verify.
"""

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import wilson  # noqa: E402


def load(spec):
    label, files = spec.split("=", 1)
    rows = []
    for f in files.split(","):
        for r in json.loads(Path(f).read_text())["results"]:
            r["_src"] = f
            rows.append(r)
    return label, rows


def pct(k, n):
    lo, hi = wilson(k, n)
    return f"{100 * k / n:.0f}% ({100 * lo:.0f}–{100 * hi:.0f})" if n else "–"


PRICE = {}  # label -> (USD per 1M input, per 1M output)


def table(rows, label=None):
    by = defaultdict(list)
    for r in rows:
        by[r["agent"]].append(r)
    metered = any(r.get("usage") for r in rows)
    head = "| agent | solved | 95% CI | false \"done\" | tampered | timeouts | median time |"
    sep = "|---|---|---|---|---|---|---|"
    if metered:
        head += " median input tok | median output tok | model calls | cost per solved |"
        sep += "---|---|---|---|"
    out = [head, sep]
    order = sorted(by, key=lambda a: -sum(r["passed"] for r in by[a]) / len(by[a]))
    for a in order:
        rs = by[a]
        k, n = sum(r["passed"] for r in rs), len(rs)
        lo, hi = wilson(k, n)
        fd = sum(bool(r.get("false_done")) for r in rs)
        tp = sum(bool(r.get("tampered")) for r in rs)
        to = sum(bool(r.get("timed_out")) for r in rs)
        med = statistics.median(r["seconds"] for r in rs)
        line = f"| {a} | {k}/{n} ({100 * k / n:.0f}%) | {100 * lo:.0f}–{100 * hi:.0f}% | {fd} | {tp} | {to} | {med:.0f}s |"
        if metered:
            us = [r["usage"] for r in rs if r.get("usage")]
            mi = statistics.median(u["input"] for u in us) if us else 0
            mo = statistics.median(u["output"] for u in us) if us else 0
            calls = statistics.median(u["requests"] for u in us) if us else 0
            pin, pout = PRICE.get(label, (0, 0))
            cost = sum(u["input"] * pin + u["output"] * pout for u in us) / 1e6
            per = f"${cost / k:.4f}" if k and (pin or pout) else "–"
            line += f" {mi:,.0f} | {mo:,.0f} | {calls:.0f} | {per} |"
        out.append(line)
    return "\n".join(out), by


def solved(rows):
    """(task, rep) -> passed, for head-to-head comparisons."""
    return {(r["task"], r.get("rep", 0)): r["passed"] for r in rows}


def head_to_head(a_rows, b_rows):
    a, b = solved(a_rows), solved(b_rows)
    common = a.keys() & b.keys()
    only_a = sum(a[k] and not b[k] for k in common)
    only_b = sum(b[k] and not a[k] for k in common)
    return len(common), only_a, only_b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, help='"Label=file.json[,file2.json]"')
    ap.add_argument("--small", help="label of the small/local-class model")
    ap.add_argument("--strong", help="label of the strong model")
    ap.add_argument("--cost", action="append", default=[], help='"Label=USD"')
    ap.add_argument("--price", action="append", default=[], help='"Label=in,out" USD per 1M tokens, for cost per solved task')
    args = ap.parse_args()
    runs = dict(load(s) for s in args.run)
    costs = dict(c.split("=", 1) for c in args.cost)
    for p in args.price:
        label, v = p.split("=", 1)
        PRICE[label] = tuple(float(x) for x in v.split(","))
    md = []
    for label, rows in runs.items():
        t, _ = table(rows, label)
        tasks = len({r["task"] for r in rows})
        cost = f", cost ${float(costs[label]):.2f}" if label in costs else ""
        md += [f"## {label}", f"{len(rows)} runs over {tasks} tasks{cost}.", "", t, ""]

    # 1. Same model, Chanto vs each other agent, head to head.
    md.append("## 1. Same model, different agents (head to head on identical tasks)")
    for label, rows in runs.items():
        by = defaultdict(list)
        for r in rows:
            by[r["agent"]].append(r)
        if "chanto" not in by:
            continue
        md += [f"**{label}:**", "", "| vs | tasks compared | only Chanto solved | only the other solved |", "|---|---|---|---|"]
        for other in sorted(a for a in by if a not in ("chanto", "chanto-verify")):
            # Compare within the same run file only.
            src = by[other][0]["_src"]
            n, a, b = head_to_head([r for r in by["chanto"] if r["_src"] == src], by[other])
            md.append(f"| {other} | {n} | {a} | {b} |")
        md.append("")

    # 2. Small model + Chanto vs strong model + others.
    if args.small in runs and args.strong in runs:
        small = defaultdict(list)
        strong = defaultdict(list)
        for r in runs[args.small]:
            small[r["agent"]].append(r)
        for r in runs[args.strong]:
            strong[r["agent"]].append(r)
        md += [f"## 2. {args.small} with Chanto vs {args.strong} with each agent", "", "| setup | solved |", "|---|---|"]
        for name, rs in [(f"{args.small} + chanto", small.get("chanto", [])), (f"{args.small} + chanto --verify", small.get("chanto-verify", []))]:
            if rs:
                md.append(f"| {name} | {pct(sum(r['passed'] for r in rs), len(rs))} |")
        for a in sorted(strong):
            rs = strong[a]
            md.append(f"| {args.strong} + {a} | {pct(sum(r['passed'] for r in rs), len(rs))} |")
        md.append("")

    # 3. Verified mode.
    md += ["## 3. Verified mode", "", "| model | plain: solved | plain: false \"done\" | --verify: solved | --verify: false \"done\" | only --verify solved | only plain solved |", "|---|---|---|---|---|---|---|"]
    for label, rows in runs.items():
        p = [r for r in rows if r["agent"] == "chanto"]
        v = [r for r in rows if r["agent"] == "chanto-verify"]
        if not (p and v):
            continue
        # Plain Chanto rows from the same run as --verify (same tasks, same conditions).
        src = v[0]["_src"]
        p = [r for r in p if r["_src"] == src]
        n, only_v, only_p = head_to_head(v, p)
        md.append(
            f"| {label} | {pct(sum(r['passed'] for r in p), len(p))} | {sum(bool(r.get('false_done')) for r in p)} | "
            f"{pct(sum(r['passed'] for r in v), len(v))} | {sum(bool(r.get('false_done')) for r in v)} | {only_v} | {only_p} |"
        )
    md += ["", "False \"done\": the agent exited successfully but the hidden check failed. CIs are 95% Wilson intervals."]
    print("\n".join(md))


if __name__ == "__main__":
    main()
