#!/usr/bin/env python3
"""CLI overhead: cold start, help, binary size and peak RSS.

    python3 extra/cli_overhead.py [--reps 10] [--repo DIR]

Measures each installed agent's `--version` and `--help` (the two paths every
CLI has), plus chanto-only paths that do not touch a model: `--run-tool Read`
and `--dump-prompt`. Timings are wall clock from spawn to exit; the first run of
each command is discarded so the numbers are warm-cache p50s.

Peak RSS comes from macOS `/usr/bin/time -l` ("maximum resident set size").
"""

import argparse
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# The Chanto checkout: a sibling of this repository unless CHANTO_REPO says otherwise.
ROOT = Path(os.environ.get("CHANTO_REPO", Path(__file__).resolve().parents[2] / "chanto")).resolve()
NPM = Path.home() / ".local/share/chanto-bench/agents/node_modules/.bin"


def resolve():
    bins = {}
    h = ROOT / "target/release/chanto"
    if h.exists():
        bins["chanto"] = str(h)
    for name in ["opencode", "claude", "forge", "codex", "kilo", "crush", "qwen"]:
        p = shutil.which(name) or (NPM / name if (NPM / name).exists() else None)
        if p:
            bins[name] = str(p)
    cline = NPM.parent / "cline/bin/cline"
    if cline.exists():
        bins["cline"] = str(cline)
    return bins


def timed(cmd, cwd, timeout=60):
    """Wall clock in milliseconds, or None on failure to launch/time out."""
    t0 = time.perf_counter()
    try:
        subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=timeout)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    return (time.perf_counter() - t0) * 1000


def rc(cmd, cwd):
    try:
        return subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=60).returncode
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def peak_rss(cmd, cwd):
    try:
        p = subprocess.run(["/usr/bin/time", "-l"] + cmd, cwd=cwd,
                           capture_output=True, text=True, timeout=60)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    m = re.search(r"(\d+)\s+maximum resident set size", p.stderr)
    return int(m.group(1)) if m else None


def p50(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def fmt(ms):
    return "–" if ms is None else f"{ms:.0f} ms"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--repo", type=Path, default=ROOT)
    args = ap.parse_args()
    # Model-free paths still resolve the configured provider first; a dummy key
    # keeps them from exiting before they do any work. A throwaway chanto home
    # keeps a user's plugins and MCP servers out of the startup number.
    os.environ.setdefault("DEEPSEEK_API_KEY", "dummy")
    home = tempfile.TemporaryDirectory(prefix="chanto-cli-")
    os.environ["CHANTO_HOME"] = home.name
    os.environ["CHANTO_NO_PRESENCE"] = "1"
    bins = resolve()
    if not bins:
        raise SystemExit("no agents found")

    sample = args.repo / "src/main.rs"
    rows = []
    for name, path in bins.items():
        # `--version` is the cheapest universal path, but not every CLI has it;
        # fall back to `--help` and say so in the table.
        startup_cmd = [path, "--version"]
        version_ok = rc(startup_cmd, args.repo) == 0
        if not version_ok:
            startup_cmd = [path, "--help"]
        help_ms = timed([path, "--help"], args.repo, 30)
        vtimes = [timed(startup_cmd, args.repo, 30) for _ in range(args.reps)]
        if vtimes and vtimes[0] is not None:
            vtimes[0] = None  # discard the cold first run
        rss = peak_rss(startup_cmd, args.repo)
        size = Path(path).resolve().stat().st_size
        row = {
            "agent": name,
            "size": size,
            "version_ok": version_ok,
            "version": p50(vtimes),
            "help": help_ms,
            "rss": rss,
        }
        if name == "chanto":
            row["run_tool"] = p50(
                [timed([path, "--run-tool", "Read",
                        '{"file_path":"src/main.rs"}'], args.repo, 60)
                 for _ in range(args.reps)]
            )
            row["dump_prompt"] = p50(
                [timed([path, "--dump-prompt"], args.repo, 60)
                 for _ in range(5)]
            )
        rows.append(row)

    print("| agent | binary MB | startup p50 | `--help` p50 | peak RSS |")
    print("|---|---|---|---|---|")
    for r in rows:
        rss = "–" if r["rss"] is None else f"{r['rss'] / 1e6:.0f} MB"
        mb = r["size"] / 1e6
        size = f"{mb:.1f}" if mb >= 0.1 else "launcher"
        v = fmt(r["version"]) + ("" if r["version_ok"] else "*")
        print(f"| {r['agent']} | {size} | {v} | "
              f"{fmt(r['help'])} | {rss} |")
    if any(not r["version_ok"] for r in rows):
        print("\n`*` that CLI has no `--version`; `--help` is used for startup.")
    if any(r["size"] / 1e6 < 0.1 for r in rows):
        print("`launcher` means the executable is a small wrapper around a JS "
              "bundle, so its own size is not the runtime's.")
    print(f"\nStartup is `--version` (or `--help` where marked `*`) p50 over "
          f"{args.reps} runs, first discarded. chanto runs with an empty "
          f"`CHANTO_HOME`, so a user's plugins and MCP servers don't skew it.")
    h = next((r for r in rows if r["agent"] == "chanto"), None)
    if h:
        print("\nChanto paths that never call a model:\n")
        print("| path | p50 |")
        print("|---|---|")
        print(f"| `--run-tool Read` | {fmt(h.get('run_tool'))} |")
        print(f"| `--dump-prompt` | {fmt(h.get('dump_prompt'))} |")
    print("\nTimings are warm-cache wall clock; the machine also ran the task "
          "benchmark, so treat differences under ~20 ms as noise.")


if __name__ == "__main__":
    main()
