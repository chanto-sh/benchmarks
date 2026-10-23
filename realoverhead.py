#!/usr/bin/env python3
"""Real-model memory/overhead per agent (trustworthy; no mock).

Runs each agent on the SAME real coding task against the SAME real model through
a LiteLLM proxy + the meter, and measures the agent's own footprint:
  - peak RSS of its whole process tree (the clean, reliable metric), and
  - CPU time (reported, but NOT a clean overhead figure on a real task — it is
    dominated by the tools the agent runs, e.g. pytest/python/git, not the agent).
Turn count comes from the meter log. Repeats --reps times and reports the median
and min-max spread.

Prefer this over stress.py for cross-agent comparison: stress.py drives a
fake mock, and some agents misbehave against it (e.g. compaction with no real
summary), so its cross-agent numbers are not trustworthy — it is for the
chanto-only build-up measurement and as a looping chanto.

Setup (model costs real money):
    ./proxy.sh deepseek/deepseek-flash          # proxy on :4700
    python3 meter.py --port 4710 --upstream http://localhost:4700 --log /tmp/m.jsonl
    python3 realoverhead.py chanto opencode claude codex --reps 3 \
            --meter http://localhost:4710 --meter-log /tmp/m.jsonl

Gotchas: the proxy's model name is `bench-model` (not the upstream id); the key
is the proxy's master_key (litellm.yaml, default sk-bench-local). Start the
proxy on a unique port and kill it by its own PID — never `pkill -f litellm`.
Covers agents that run a tool loop over OpenAI chat / Anthropic messages / OpenAI
Responses. aider runs no tool loop and isn't driven here.
"""
import argparse, importlib.util, json, os, re, shutil, statistics, subprocess, sys, tempfile, threading, time, uuid
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASK = ("Create calc.py with add, subtract, multiply and divide (divide by zero raises ValueError); "
        "a main.py CLI that computes 'A op B' from argv; and pytest tests in test_calc.py. "
        "Run the tests and make sure they pass.")


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
        kids[int(q[1])].append(int(q[0]))
        r[int(q[0])] = int(q[2])
    tot, st = 0, [root]
    while st:
        x = st.pop()
        tot += r.get(x, 0)
        st += kids.get(x, [])
    return tot


def one_run(run, agent, meter, meter_log, model, home):
    label = f"{agent}~real~{uuid.uuid4().hex[:8]}"
    run.API = f"{meter}/{label}"
    wd = home / "w" / agent
    shutil.rmtree(wd, ignore_errors=True)
    wd.mkdir(parents=True)
    try:
        cmd, extra = run.hosted_cmd(agent, model, TASK, 200000, wd)
    except Exception:
        return None
    env = dict(os.environ, **extra)
    env["PWD"] = str(wd)
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        if k not in extra:
            env.pop(k, None)
    time_bin = shutil.which("gtime") or "/usr/bin/time"
    p = subprocess.Popen([time_bin, "-l"] + cmd, cwd=wd, env=env, stdout=subprocess.DEVNULL,
                         stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, text=True)
    rss = []

    def poll():
        while p.poll() is None:
            v = tree_rss(p.pid)
            if v:
                rss.append(v)
            time.sleep(0.1)

    th = threading.Thread(target=poll)
    th.start()
    try:
        _, err = p.communicate(timeout=300)
    except subprocess.TimeoutExpired:
        p.kill()
        _, err = p.communicate()
    th.join()
    m = re.search(r'([\d.]+)\s+real\s+([\d.]+)\s+user\s+([\d.]+)\s+sys', err or "")
    cpu = (float(m.group(2)) + float(m.group(3))) if m else None
    calls = sum(1 for l in open(meter_log) if l.strip() and json.loads(l).get("label") == label)
    return {"turns": calls, "cpu": cpu, "rss": (max(rss) / 1024) if rss else 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agents", nargs="*", default=["chanto", "opencode", "goose", "crush", "qwen", "kilo", "pi"])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--meter", default="http://localhost:4710")
    ap.add_argument("--meter-log", default="/tmp/mymeter.jsonl")
    ap.add_argument("--model", default="bench-model")
    ap.add_argument("--key", default="sk-bench-local")
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("br", ROOT / "run.py")
    run = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run)
    run.API_KEY = a.key
    home = Path(tempfile.mkdtemp(prefix="realoh-"))
    (home / "w").mkdir()
    run.WORK = home / "w"
    print(f"REAL model via {a.meter}, {a.reps} reps/agent; peak RSS is the clean metric\n")
    print(f"{'agent':10} {'turns':>6}  {'peak RSS MB med [min-max]':>26}  {'CPU s*':>8}")
    for agent in a.agents:
        runs = [one_run(run, agent, a.meter, a.meter_log, a.model, home) for _ in range(a.reps)]
        ok = [r for r in runs if r and r["turns"]]
        if not ok:
            print(f"{agent:10} {'—':>6}  0 model calls (wire/proxy not supported)")
            continue
        rss = sorted(r["rss"] for r in ok)
        cpu = [r["cpu"] for r in ok if r["cpu"]]
        t = statistics.median(r["turns"] for r in ok)
        cpus = f"{statistics.median(cpu):.1f}" if cpu else "?"
        print(f"{agent:10} {t:6.0f}  {statistics.median(rss):5.0f} [{min(rss):.0f}-{max(rss):.0f}]{'':>11}  {cpus:>8}", flush=True)
    print("\n*CPU includes the tools the agent runs (pytest/python/git); not a clean agent-overhead metric.")
    shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    main()
