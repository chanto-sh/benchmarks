#!/usr/bin/env python3
"""Measure chanto's OWN per-turn overhead and memory as a session gets long.

Drives chanto through N tool-call turns against the instant mock model
(tests/chaos/fakemodel.py), so the model's own time is ~0 and the gap between
consecutive model requests is pure chanto compute: prompt assembly, tool
execution, context handling. Each turn reads a different file, so loop
detection doesn't stop it and the conversation genuinely grows.

Two modes expose the whole story:
  --blob-kb 50                big tool outputs, unbounded context: the build-up
  --blob-kb 50 --num-ctx 32768  bounded context: compaction caps it (plateau)

    python3 overhead.py [--turns 100] [--blob-kb 1] [--num-ctx N]
                              [--bin ../chanto/target/release/chanto]

Reports per-turn overhead (ms, bucketed) and peak RSS. Free: no real model.
"""
import argparse, json, os, subprocess, sys, tempfile, threading, time, statistics
from pathlib import Path

# The Chanto checkout: its release binary and its test model server. A sibling
# clone unless CHANTO_REPO says otherwise.
CHANTO_REPO = Path(os.environ.get("CHANTO_REPO", Path(__file__).resolve().parent.parent / "chanto"))
FAKE = CHANTO_REPO / "tests/chaos/fakemodel.py"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=100)
    ap.add_argument("--blob-kb", type=int, default=1, help="KB added to history per turn")
    ap.add_argument("--num-ctx", type=int, default=0, help="0 = leave unbounded")
    ap.add_argument("--bin", default=str(CHANTO_REPO / "target/release/chanto"))
    a = ap.parse_args()

    wd = Path(tempfile.mkdtemp(prefix="chanto-overhead-"))
    (wd / "home").mkdir()
    blob = ("lorem ipsum dolor sit amet " * 40 + "\n")  # ~1 KB/line
    for i in range(a.turns + 20):
        (wd / f"f{i}.txt").write_text(f"file {i}\n" + blob * a.blob_kb)

    scen = wd / "scenario.py"
    scen.write_text(
        "import json\n"
        "def respond(body, n):\n"
        "    pt = max(1, len(json.dumps(body)) // 4)\n"
        "    u = {'usage': {'prompt_tokens': pt, 'completion_tokens': 5}}\n"
        f"    if n < {a.turns}:\n"
        "        return {**u, 'tool_calls': [{'name': 'Read', 'args': {'file_path': f'f{n}.txt'}}],\n"
        "                'finish_reason': 'tool_calls'}\n"
        "    return {**u, 'text': 'done.'}\n"
    )
    log = wd / "model.log"
    log.write_text("")
    args = [sys.executable, str(FAKE), str(scen), "--log", str(log)]
    if a.num_ctx:
        args += ["--ctx", str(a.num_ctx)]
    mock = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    port = None
    t0 = time.time()
    while time.time() - t0 < 5:
        line = mock.stdout.readline()
        if line.startswith("PORT"):
            port = line.split()[1]
            break
    if not port:
        sys.exit("mock did not start")

    env = {
        "PATH": os.environ["PATH"], "HOME": str(wd), "CHANTO_HOME": str(wd / "home"),
        "CHANTO_PROVIDER": "openai", "CHANTO_BASE_URL": f"http://127.0.0.1:{port}/v1",
        "CHANTO_MODEL": "fake",
    }
    cmd = [a.bin, "-p", "read the files as I direct", "--cwd", str(wd)]
    if a.num_ctx:
        cmd += ["--num-ctx", str(a.num_ctx)]
    p = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rss = []

    def poll():
        while p.poll() is None:
            try:
                rss.append(int(subprocess.check_output(["ps", "-o", "rss=", "-p", str(p.pid)]).strip()))
            except Exception:
                pass
            time.sleep(0.1)

    th = threading.Thread(target=poll)
    th.start()
    p.wait()
    th.join()
    mock.kill()

    ts = [json.loads(l)["t"] for l in log.read_text().splitlines() if l.strip()
          and json.loads(l).get("kind") == "chat"]
    gaps = [(ts[i + 1] - ts[i]) * 1000 for i in range(len(ts) - 1)]
    ctx = f"num_ctx={a.num_ctx}" if a.num_ctx else "unbounded context"
    print(f"chanto overhead: {len(ts)} turns, {a.blob_kb} KB/turn, {ctx}")
    for lo in range(0, len(gaps), 20):
        seg = gaps[lo:lo + 20]
        print(f"  turns {lo+1:3d}-{lo+len(seg):3d}: median {statistics.median(seg):6.1f} ms")
    if gaps:
        print(f"  first 5 {statistics.median(gaps[:5]):.1f} ms -> last 5 {statistics.median(gaps[-5:]):.1f} ms")
    if rss:
        print(f"  peak RSS: {max(rss)/1024:.0f} MB")
    import shutil
    shutil.rmtree(wd, ignore_errors=True)


if __name__ == "__main__":
    main()
