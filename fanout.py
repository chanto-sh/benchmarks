#!/usr/bin/env python3
"""What fanning out to many subagents costs each agent, against fanmock.py.

    python3 fanout.py --agents chanto,claude,codex,opencode --fan 1,6,20,100

Peak memory and processes are of the whole process tree; CPU includes every
process it started. A run counts as complete only if every subagent finished.
Agents queue past their own limits, so peak memory at high N partly shows the
limit and not only the cost: `peak live` says how many subagents were running.
"""
import argparse, json, os, statistics, subprocess, sys, tempfile, threading, time
from pathlib import Path

import cputurn

run = cputurn.run
ROOT = Path(__file__).resolve().parent
PROMPT = "FANOUT-ROOT: start the subagents the task needs, then report."


def one(agent, fan, delay, limit, base):
    home = Path(tempfile.mkdtemp(prefix=f"fan-{agent}-", dir=base)).resolve()
    wd = home / "work"
    wd.mkdir()
    (wd / "big.txt").write_text("a line of text in a file\n" * 1600)
    subprocess.run(["git", "init", "-q"], cwd=wd)
    log = home / "mock.jsonl"
    log.write_text("")
    mock = subprocess.Popen([sys.executable, str(ROOT / "fanmock.py"), "--agents", str(fan), "--delay", str(delay), "--limit", str(limit),
                             "--log", str(log)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    port = mock.stdout.readline().split()[1]
    run.API = f"http://127.0.0.1:{port}"
    cmd, extra = run.hosted_cmd(agent, "fake", PROMPT, 200000, wd)
    env = dict(os.environ, **extra)
    env["PWD"] = str(wd)
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        if k not in extra:
            env.pop(k, None)
    start = time.time()
    p = subprocess.Popen(cmd, cwd=wd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=open(home / "stderr", "w"), start_new_session=True)
    seen, peak, stop = {}, [0], threading.Event()

    def sample():
        while not stop.is_set():
            peak[0] = max(peak[0], cputurn.sample_tree_cpu(p.pid, seen))
            time.sleep(0.06)

    th = threading.Thread(target=sample)
    th.start()
    cpu = cputurn.wait_rusage(p, limit)
    wall = time.time() - start
    stop.set()
    th.join()
    timed_out = p.returncode is None or wall >= limit
    code = p.returncode
    time.sleep(1)
    left = subprocess.run(["pgrep", "-g", str(p.pid)], capture_output=True, text=True).stdout.split()
    if left:
        subprocess.run(["pkill", "-9", "-g", str(p.pid)])
    mock.kill()
    mock.wait()
    entries = [json.loads(l) for l in log.read_text().splitlines()]
    last = entries[-1] if entries else {}
    result = {
        "agent": agent, "fan": fan, "finished": last.get("finished", 0), "started": last.get("started", 0),
        "requests": len(entries), "cpu_ms": cpu * 1000 if cpu is not None else None,
        "peak_mb": peak[0] / 1024, "processes": len(seen), "wall_s": wall, "overhead_s": None,
        "exit": code, "timed_out": timed_out, "left_running": len(left),
        "no_tool": any(e.get("text") == "NO-SUBAGENT-TOOL" for e in entries),
        "tools": (entries[0].get("tools") if entries else None),
        "stderr": (home / "stderr").read_text(errors="replace")[-300:],
    }
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agents", default="chanto")
    ap.add_argument("--fan", default="1,6,20")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--delay", type=float, default=0.5)
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--json")
    a = ap.parse_args()
    results = []
    base = tempfile.mkdtemp(prefix="fanout-")
    print("| agent | N | finished | peak MB | MB/agent | CPU ms | ms/agent | processes | wall s | left running | exit |")
    print("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for agent in a.agents.split(","):
        floor = None
        for fan in [int(x) for x in a.fan.split(",")]:
            rows = [one(agent, fan, a.delay, a.limit, base) for _ in range(a.reps)]
            results += rows
            med = lambda k: statistics.median(r[k] or 0 for r in rows)
            peak = max(r["peak_mb"] for r in rows)
            if rows[0]["no_tool"]:
                print(f"| {agent} | {fan} | no subagent tool the mock recognises: {rows[0]['tools']} |", flush=True)
                break
            if floor is None:
                floor = (peak, med("cpu_ms"), fan)
            per = lambda v, f: f"{(v - f) / (fan - floor[2]):.2f}" if fan > floor[2] else "—"
            print(f"| {agent} | {fan} | {min(r['finished'] for r in rows)}/{fan} | {peak:.0f} | {per(peak, floor[0])} | "
                  f"{med('cpu_ms'):.0f} | {per(med('cpu_ms'), floor[1])} | {max(r['processes'] for r in rows)} | "
                  f"{med('wall_s'):.1f} | {max(r['left_running'] for r in rows)} | {rows[0]['exit']} |", flush=True)
            if not all(r["finished"] for r in rows) or rows[0]["timed_out"]:
                print(f"  {agent} stderr: {rows[0]['stderr'][-200:]!r}", flush=True)
    if a.json:
        Path(a.json).write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
