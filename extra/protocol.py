#!/usr/bin/env python3
"""Protocol conformance: the non-interactive surfaces SDKs and editors use.

    python3 extra/protocol.py [--no-model]

Checks, against the wire contracts the docs promise:

- `mcp-serve`: JSON-RPC initialize, initialization notification, tools/list,
  and a tools/call round trip over stdio.
- `acp`: ACP initialize (Zed/JetBrains).
- `-p --output-format json`: one result object with the documented fields.
- `-p --output-format stream-json`: one JSON object per line, ending in a
  `result` event; every line is valid JSON.
- `--input-format stream-json`: a user message on stdin runs a turn and the
  result comes back on stdout.
- exit codes: a bad flag is a usage error, `--help` is success.

Model-backed checks use the same OpenAI-compatible proxy as `run.py`
(BENCH_PROVIDER / BENCH_BASE_URL / BENCH_MODEL / BENCH_API_KEY, or --no-model).
"""

import argparse
import json
import os
import queue
import subprocess
import tempfile
import threading
import time
from pathlib import Path

# The Chanto checkout: a sibling of this repository unless CHANTO_REPO says otherwise.
ROOT = Path(os.environ.get("CHANTO_REPO", Path(__file__).resolve().parents[2] / "chanto")).resolve()
BIN = ROOT / "target/debug/chanto"  # the working tree, not the benchmark release

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, ok, detail))
    print(f"| {name} | {'pass' if ok else 'FAIL'} | {detail} |")


def env(home):
    e = dict(os.environ)
    e.update({
        "CHANTO_HOME": home,
        "CHANTO_NO_PRESENCE": "1",
        "DEEPSEEK_API_KEY": "dummy",
    })
    return e


class Reader:
    """One pump thread per process, and `wait_for` on its JSON-RPC replies."""

    def __init__(self, proc):
        self.q = queue.Queue()
        threading.Thread(target=self._pump, args=(proc,), daemon=True).start()

    def _pump(self, proc):
        for line in proc.stdout:
            self.q.put(line)
        self.q.put(None)

    def wait_for(self, want_id, timeout=10):
        end = time.monotonic() + timeout
        while True:
            left = end - time.monotonic()
            if left <= 0:
                return None
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                return None
            if line is None:
                return None
            try:
                m = json.loads(line)
            except json.JSONDecodeError:
                continue
            if m.get("id") == want_id:
                return m


def jsonrpc(proc, msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()


def mcp(home):
    proc = subprocess.Popen(
        [str(BIN), "mcp-serve"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, cwd=ROOT, env=env(home),
    )
    try:
        reader = Reader(proc)
        jsonrpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": "2024-11-05",
                                  "capabilities": {},
                                  "clientInfo": {"name": "bench", "version": "0"}}})
        init = reader.wait_for(1)
        check("mcp: initialize", bool(init and init.get("result", {}).get("serverInfo")),
              (init or {}).get("result", {}).get("protocolVersion", "no reply"))
        jsonrpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        jsonrpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        listed = reader.wait_for(2)
        tools = (listed or {}).get("result", {}).get("tools", [])
        check("mcp: tools/list", bool(tools) and all("inputSchema" in t for t in tools),
              f"{len(tools)} tools")
        name = "Read" if any(t["name"] == "Read" for t in tools) else (
            tools[0]["name"] if tools else "")
        jsonrpc(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                       "params": {"name": name, "arguments": {"file_path": "README.md"}}})
        called = reader.wait_for(3, 20)
        ok = bool((called or {}).get("result", {}).get("content"))
        check("mcp: tools/call", ok, name or "no tool")
    finally:
        proc.kill()


def acp(home):
    proc = subprocess.Popen(
        [str(BIN), "acp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, cwd=ROOT, env=env(home),
    )
    try:
        reader = Reader(proc)
        jsonrpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": 1, "clientCapabilities": {}}})
        got = reader.wait_for(1)
        info = (got or {}).get("result", {}).get("agentInfo", {})
        check("acp: initialize", info.get("name") == "chanto", f"protocolVersion "
              f"{(got or {}).get('result', {}).get('protocolVersion')}")
        # An unknown session must be a JSON-RPC error, not a crash.
        jsonrpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "session/prompt",
                       "params": {"sessionId": "nope", "prompt": []}})
        bad = reader.wait_for(2)
        check("acp: unknown session errors", bool((bad or {}).get("error")),
              (bad or {}).get("error", {}).get("message", "no reply")[:60])
        check("acp: still alive", proc.poll() is None, f"exit {proc.poll()}")
    finally:
        proc.kill()


def model_args(args):
    a = [str(BIN), "-p"]
    if args.provider:
        a += ["--provider", args.provider]
    if args.base_url:
        a += ["--base-url", args.base_url]
    if args.model:
        a += ["--model", args.model]
    a += ["--mode", "bypassPermissions"]
    return a


def model_env(home, args):
    e = env(home)
    if args.api_key:
        e["CHANTO_API_KEY"] = args.api_key
    return e


RESULT_FIELDS = {"type", "is_error", "result", "duration_ms", "num_turns",
                 "tool_calls", "total_cost_usd", "usage", "session_id", "model"}


def json_output(home, args):
    p = subprocess.run(model_args(args) + ["--output-format", "json",
                                           "Reply with exactly: ok"],
                       capture_output=True, text=True, cwd=ROOT,
                       env=model_env(home, args), timeout=180)
    try:
        d = json.loads(p.stdout)
    except json.JSONDecodeError:
        check("json: one object", False, p.stderr.strip()[:70] or p.stdout[:70])
        return
    check("json: one object", isinstance(d, dict) and d.get("type") == "result",
          d.get("type", "?"))
    missing = RESULT_FIELDS - set(d)
    check("json: documented fields", not missing,
          f"missing {sorted(missing)}" if missing else "all present")
    check("json: no error", d.get("is_error") is False and p.returncode == 0,
          f"exit {p.returncode}")


def stream_output(home, args):
    p = subprocess.run(model_args(args) + ["--output-format", "stream-json",
                                           "Reply with exactly: ok"],
                       capture_output=True, text=True, cwd=ROOT,
                       env=model_env(home, args), timeout=180)
    lines = [l for l in p.stdout.splitlines() if l.strip()]
    parsed = []
    for l in lines:
        try:
            parsed.append(json.loads(l))
        except json.JSONDecodeError:
            check("stream: every line is JSON", False, l[:70])
            return
    check("stream: every line is JSON", bool(parsed), f"{len(parsed)} events")
    final = parsed[-1] if parsed else {}
    check("stream: ends in result", final.get("type") == "result",
          final.get("type", "none"))
    check("stream: result has fields", RESULT_FIELDS <= set(final),
          "all present" if RESULT_FIELDS <= set(final) else
          f"missing {sorted(RESULT_FIELDS - set(final))}")


def stream_input(home, args):
    msg = json.dumps({"type": "user", "session_id": "s",
                      "message": {"role": "user", "content": [
                          {"type": "text", "text": "Reply with exactly: ok"}]}})
    p = subprocess.run(
        model_args(args) + ["--output-format", "stream-json",
                            "--input-format", "stream-json"],
        input=msg + "\n", capture_output=True, text=True, cwd=ROOT,
        env=model_env(home, args), timeout=180)
    lines = [l for l in p.stdout.splitlines() if l.strip()]
    events = []
    for l in lines:
        try:
            events.append(json.loads(l))
        except json.JSONDecodeError:
            check("stream-in: every line is JSON", False, l[:70])
            return
    check("stream-in: one turn per line", bool(events), f"{len(events)} events")
    final = events[-1] if events else {}
    check("stream-in: result", final.get("type") == "result" and
          final.get("is_error") is False, final.get("type", "none"))


def exit_codes(home):
    bad = subprocess.run([str(BIN), "--definitely-not-a-flag"],
                         capture_output=True, text=True, cwd=ROOT, env=env(home))
    check("cli: bad flag is a usage error", bad.returncode in (1, 2),
          f"exit {bad.returncode}")
    ok = subprocess.run([str(BIN), "--help"], capture_output=True, text=True,
                        cwd=ROOT, env=env(home))
    check("cli: --help exits 0", ok.returncode == 0, f"exit {ok.returncode}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-model", action="store_true")
    ap.add_argument("--provider", default=os.environ.get("BENCH_PROVIDER"))
    ap.add_argument("--base-url", default=os.environ.get("BENCH_BASE_URL"))
    ap.add_argument("--model", default=os.environ.get("BENCH_MODEL"))
    ap.add_argument("--api-key", default=os.environ.get("BENCH_API_KEY"))
    args = ap.parse_args()
    if not BIN.exists():
        raise SystemExit(f"{BIN} is missing; build it with `cargo build`")

    print("| check | result | detail |")
    print("|---|---|---|")
    with tempfile.TemporaryDirectory(prefix="chanto-protocol-") as home:
        mcp(home)
        acp(home)
        exit_codes(home)
        if not args.no_model:
            json_output(home, args)
            stream_output(home, args)
            stream_input(home, args)
    failed = [name for name, ok, _ in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks pass")
    if failed:
        print("\nfailed: " + ", ".join(failed))


if __name__ == "__main__":
    main()
