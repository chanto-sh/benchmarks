#!/usr/bin/env python3
"""Stress comparison of coding agents' OWN overhead under a long, growing
session. Each agent is driven through many turns where every turn reads a large
file, so the conversation grows (the shape of a future high-context, many-turn
run). An instant mock model (stressmock.py) answers in ~0 time, so the gap
between an agent's model requests is its own compute and the process-tree peak
RSS is its own memory. Reuses run.py's per-agent --api configs.

    python3 stress.py [agents...] [--reps 5] [--turns 40] [--blob-kb 50]

Runs each agent --reps times and reports the median (and min–max spread) of
per-turn overhead and peak memory.

CAVEAT — not trustworthy for cross-agent comparison: the mock returns canned
tool-calls, never real text or summaries, so agents misbehave against it (e.g.
opencode's compaction fails with "no summary" and it quits). And peak memory
here reflects each runtime's footprint, not whether it compacts (most of these
do compact). For a real cross-agent memory comparison use realoverhead.py
(real model). This script is best for the chanto-only build-up measurement
(overhead.py is the focused version) and as a looping chanto.

Drives agents that loop over OpenAI /chat/completions, Anthropic /messages or
OpenAI Responses (incl. codex and Claude Code); aider runs no tool loop. The
model is excluded by construction.
"""
import argparse, importlib.util, json, os, shutil, statistics, subprocess, sys, tempfile, threading, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MOCK = Path(__file__).resolve().parent / "stressmock.py"
spec = importlib.util.spec_from_file_location("benchrun", ROOT / "run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


def start_mock(turns, log):
    p = subprocess.Popen([sys.executable, str(MOCK), "--turns", str(turns), "--log", str(log)],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    t0 = time.time()
    while time.time() - t0 < 5:
        line = p.stdout.readline()
        if line.startswith("PORT"):
            return p, line.split()[1]
    p.kill()
    return None, None


def tree_rss(root):
    try:
        out = subprocess.check_output(["ps", "-o", "pid=,ppid=,rss=", "-A"], text=True)
    except Exception:
        return 0
    kids, r = defaultdict(list), {}
    for ln in out.splitlines():
        q = ln.split()
        if len(q) < 3:
            continue
        pid_, pp_, rs_ = int(q[0]), int(q[1]), int(q[2])
        kids[pp_].append(pid_)
        r[pid_] = rs_
    tot, st = 0, [root]
    while st:
        x = st.pop()
        tot += r.get(x, 0)
        st += kids.get(x, [])
    return tot


def one_run(agent, home, turns, blob_kb):
    log = home / f"{agent}.jsonl"
    log.write_text("")
    mock, port = start_mock(turns, log)
    if not port:
        return None
    run.API = f"http://127.0.0.1:{port}"
    wd = home / "work" / agent
    shutil.rmtree(wd, ignore_errors=True)
    wd.mkdir(parents=True)
    blob = ("lorem ipsum dolor sit amet " * 40 + "\n")
    for i in range(turns + 20):
        (wd / f"f{i}.txt").write_text(f"file {i}\n" + blob * blob_kb)
    try:
        cmd, extra = run.hosted_cmd(agent, "fake", "Read each file I point you to, in order.", 200000, wd)
    except Exception:
        mock.kill()
        return None
    env = dict(os.environ, **extra)
    env["PWD"] = str(wd)
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        if k not in extra:
            env.pop(k, None)
    p = subprocess.Popen(cmd, cwd=wd, env=env, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    rss = []

    def poll():
        while p.poll() is None:
            v = tree_rss(p.pid)
            if v:
                rss.append(v)
            time.sleep(0.15)

    th = threading.Thread(target=poll)
    th.start()
    try:
        p.wait(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill()
    th.join()
    mock.kill()
    ts = [json.loads(l)["t"] for l in log.read_text().splitlines() if l.strip()]
    if len(ts) < 4:
        return {"turns": len(ts), "overhead": None, "rss": (max(rss) / 1024) if rss else 0}
    g = [(ts[i + 1] - ts[i]) * 1000 for i in range(len(ts) - 1)]
    return {"turns": len(ts), "overhead": statistics.median(g), "rss": (max(rss) / 1024) if rss else 0}


def agg(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return "n/a"
    return f"{statistics.median(vals):.0f} [{min(vals):.0f}-{max(vals):.0f}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agents", nargs="*",
                    default=["chanto", "opencode", "goose", "crush", "qwen", "kilo", "pi", "claude"])
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--turns", type=int, default=40)
    ap.add_argument("--blob-kb", type=int, default=50)
    a = ap.parse_args()
    home = Path(tempfile.mkdtemp(prefix="stress-"))
    (home / "work").mkdir()
    run.WORK = home / "work"
    run.API_KEY = "x"
    print(f"STRESS: {a.turns} turns, {a.blob_kb} KB/turn, {a.reps} reps per agent (model instant)\n")
    print(f"{'agent':10} {'turns':>6}  {'overhead ms/turn':>22}  {'peak RSS MB':>20}")
    results = {}
    for agent in a.agents:
        runs = [one_run(agent, home, a.turns, a.blob_kb) for _ in range(a.reps)]
        runs = [r for r in runs if r]
        if not runs:
            print(f"{agent:10} {'—':>6}  {'did not run':>22}")
            continue
        turns = statistics.median(r["turns"] for r in runs)
        oh = agg([r["overhead"] for r in runs])
        rs = agg([r["rss"] for r in runs])
        results[agent] = {"turns": turns, "overhead": oh, "rss": rs}
        print(f"{agent:10} {turns:6.0f}  {oh:>22}  {rs:>20}", flush=True)
    (home / "..").resolve()
    print("\n(median [min-max] across reps)")
    shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    main()
