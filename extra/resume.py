#!/usr/bin/env python3
"""Interrupt/resume robustness.

    python3 extra/resume.py

Starts a print-mode turn that runs a long Bash command, sends SIGINT while the
tool is running, and checks that:

- the process stops promptly (no hang, no orphaned child processes);
- the session on disk is still resumable;
- `--resume <id>` finishes a turn and keeps the same session id.

The point is the failure mode users hit daily: Ctrl-C during a tool call. A
chanto that loses the session, leaves `sleep` running, or needs a restart is
not usable for long tasks.

Uses the same proxy env as `run.py` (BENCH_PROVIDER / BENCH_BASE_URL /
BENCH_MODEL / BENCH_API_KEY).
"""

import argparse
import json
import os
import queue
import signal
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path

# The Chanto checkout: a sibling of this repository unless CHANTO_REPO says otherwise.
ROOT = Path(os.environ.get("CHANTO_REPO", Path(__file__).resolve().parents[2] / "chanto")).resolve()
BIN = ROOT / "target/debug/chanto"
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, ok))
    print(f"| {name} | {'pass' if ok else 'FAIL'} | {detail} |")


def children(pid):
    out = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True)
    return [int(x) for x in out.stdout.split()]


def sleepers():
    out = subprocess.run(["pgrep", "-f", "sleep 30"], capture_output=True, text=True)
    return set(int(x) for x in out.stdout.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default=os.environ.get("BENCH_PROVIDER"))
    ap.add_argument("--base-url", default=os.environ.get("BENCH_BASE_URL"))
    ap.add_argument("--model", default=os.environ.get("BENCH_MODEL"))
    ap.add_argument("--api-key", default=os.environ.get("BENCH_API_KEY"))
    ap.add_argument("--timeout", type=float, default=90, help="seconds to reach the tool call")
    args = ap.parse_args()
    if not BIN.exists():
        raise SystemExit(f"{BIN} is missing; build it with `cargo build`")

    print("| check | result | detail |")
    print("|---|---|---|")
    sid = str(uuid.uuid4())
    with tempfile.TemporaryDirectory(prefix="chanto-resume-") as home:
        env = dict(os.environ)
        env.update({
            "CHANTO_HOME": home, "CHANTO_NO_PRESENCE": "1",
            "DEEPSEEK_API_KEY": "dummy",
        })
        if args.api_key:
            env["CHANTO_API_KEY"] = args.api_key
        argv = [str(BIN), "-p", "--session-id", sid,
                "--output-format", "stream-json", "--mode", "bypassPermissions"]
        if args.provider:
            argv += ["--provider", args.provider]
        if args.base_url:
            argv += ["--base-url", args.base_url]
        if args.model:
            argv += ["--model", args.model]
        argv.append("Run `sleep 30` with the Bash tool, wait for it, then reply "
                    "with exactly: done")
        before = sleepers()
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, cwd=ROOT, env=env, start_new_session=True)
        q = queue.Queue()

        def pump():
            for line in proc.stdout:
                q.put(line)
            q.put(None)

        threading.Thread(target=pump, daemon=True).start()
        saw_tool = False
        end = time.monotonic() + args.timeout
        while time.monotonic() < end:
            try:
                line = q.get(timeout=max(0.1, end - time.monotonic()))
            except queue.Empty:
                break
            if line is None:
                break
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "tool_start" and "Bash" in ev.get("label", ""):
                saw_tool = True
                break
        check("tool call reached", saw_tool, "Bash started" if saw_tool else "no Bash tool call")

        t0 = time.monotonic()
        if saw_tool:
            os.killpg(proc.pid, signal.SIGINT)
        try:
            rc = proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            rc = "hung"
        dt = time.monotonic() - t0
        check("SIGINT stops the turn", rc != "hung" and dt < 10,
              f"exit {rc} in {dt:.1f}s")

        time.sleep(1)
        left = sleepers() - before
        check("no orphaned child", not left,
              f"{len(left)} left running" if left else "none")

        # The session id we named must still be there and resume.
        sessions = list(Path(home).rglob(f"*{sid}*"))
        check("session saved", bool(sessions), f"{len(sessions)} file(s)")

        resumed = subprocess.run(
            [str(BIN), "-p", "--resume", sid, "--output-format", "json"]
            + (["--provider", args.provider] if args.provider else [])
            + (["--base-url", args.base_url] if args.base_url else [])
            + (["--model", args.model] if args.model else [])
            + ["--mode", "bypassPermissions", "Reply with exactly: resumed"],
            capture_output=True, text=True, cwd=ROOT, env=env, timeout=180)
        try:
            d = json.loads(resumed.stdout)
        except json.JSONDecodeError:
            d = {}
        check("resume finishes a turn",
              resumed.returncode == 0 and d.get("type") == "result"
              and d.get("is_error") is False,
              f"exit {resumed.returncode}")
        check("resume keeps the session id", d.get("session_id") == sid,
              d.get("session_id", "none"))

    failed = [n for n, ok in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks pass")
    if failed:
        print("\nfailed: " + ", ".join(failed))


if __name__ == "__main__":
    main()
