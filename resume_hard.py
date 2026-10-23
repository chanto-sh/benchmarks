#!/usr/bin/env python3
"""Resume the paused October 2026 hard-tier benchmark (paths are the benchmark
machine's): run only the (agent, task) pairs with no
PASS/FAIL line in any hard-*.log yet. Main agents first, then the follow-up ones.
Usage: python3 resume_hard.py [--dry-run]"""
import json, os, re, subprocess, sys, time
from pathlib import Path

L = Path.home() / ".local/share/chanto-bench/logs"
REPO = Path(__file__).resolve().parent
MAIN = ["chanto", "chanto-verify", "claude", "codex", "opencode", "pi", "goose"]
EXTRA = ["qwen", "kilo", "crush", "aider"]
tasks = [t for t in (L / "hard-tasks.txt").read_text().split() if t]
# What's done is what the result files hold, not the logs: a run whose result
# couldn't be written (the disk filled up once) is printed but not recorded.
done = set()
for f in sorted((REPO / "results").glob("2026101*.json")):
    if f.name >= "20261013-232700":  # the hard tier, after the voided first attempt
        try:
            done |= {(r["agent"], r["task"]) for r in json.loads(f.read_text())["results"]}
        except (ValueError, KeyError):
            pass

def missing(agents):
    """task -> agents still to run, grouped so each run.py call shares one agent list."""
    groups = {}
    for t in tasks:
        need = tuple(a for a in agents if (a, t) not in done)
        if need:
            groups.setdefault(need, []).append(t)
    return groups

plan = [g for agents in (MAIN, EXTRA) for g in missing(agents).items()]
for agents, ts in plan:
    print(f"{','.join(agents)}: {len(ts)} task(s)")
if "--dry-run" in sys.argv or not plan:
    sys.exit(0)

# Proxy and meter, as for the original run.
def up(port):
    return subprocess.run(["curl", "-sf", "-o", "/dev/null", f"localhost:{port}/health/liveliness" if port == 4000 else f"localhost:{port}/"]).returncode == 0
if not up(4000):
    subprocess.Popen(f"nohup ./proxy.sh deepseek/deepseek-flash >> {L}/proxy-hard.log 2>&1 &", shell=True, cwd=REPO, start_new_session=True)
if not up(4100):
    subprocess.Popen(f"nohup python3 meter.py --port 4100 --upstream http://localhost:4000 --log {L}/meter-hard.jsonl >> {L}/meter-hard.out 2>&1 &", shell=True, cwd=REPO, start_new_session=True)
for _ in range(60):
    if up(4000) and up(4100):
        break
    time.sleep(1)
else:
    sys.exit("proxy or meter didn't start")

# Two shards; each runs its share of the plan in order.
env = dict(os.environ, BENCH_CHANTO_BIN=str(Path.home() / ".local/share/chanto-bench/bin/chanto-cb06a06"))
common = ["--api", "http://localhost:4000", "--meter", "http://localhost:4100", "--meter-log", str(L / "meter-hard.jsonl"),
          "--model", "bench-model", "--ctx", "131072", "--timeout", "1200", "--min-balance", "1", "--offline"]
stamp = time.strftime("%m%d%H%M")
for shard in (0, 1):
    work = Path.home() / f".local/share/chanto-bench/work-resume-{shard}"
    steps = []
    for n, (agents, ts) in enumerate(plan):
        mine = ts[shard::2]
        if mine:
            steps.append(f"rm -rf {work}; BENCH_WORK={work} python3 run.py {' '.join(common)} --seed {200 + 10 * n + shard} "
                         f"--agents {','.join(agents)} --tasks {','.join(mine)}")
    if steps:
        subprocess.Popen(["bash", "-c", "; ".join(steps)], cwd=REPO, env=env, start_new_session=True,
                         stdout=open(L / f"hard-r{stamp}-{shard}.log", "w"), stderr=subprocess.STDOUT)
print(f"started; logs: {L}/hard-r{stamp}-*.log")
