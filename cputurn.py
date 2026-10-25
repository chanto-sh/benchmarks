#!/usr/bin/env python3
"""Cross-agent per-turn CPU comparison.

Measures each coding agent's OWN CPU cost per turn — the compute it spends
parsing a response, running its tool, and rebuilding context — with the model
excluded by construction (an instant mock, stressmock.py, answers in ~0
time). CPU time, not the wall-clock gap between requests: the gap counts idle
and scheduling, CPU time counts only work, so it is the honest "overhead".

Nothing is instrumented or rebuilt. CPU is read from the kernel's rusage from
OUTSIDE each process, identically for every runtime (Rust/Node/Bun/Python):
  - wait4() on the agent reports user+sys for the process and every child it
    reaped (one number, the headline metric; what `/usr/bin/time` prints, and
    the same call on macOS and Linux);
  - a 60 ms poll of `ps -o pid,ppid,time` over the process tree tracks each
    pid's max cumulative CPU and sums them (a cross-check that also catches
    short-lived tool children). The two should agree within noise.

    python3 cputurn.py [agents...] [--reps 3] [--turns 40] [--blob-kb 50]

Reports median [min-max] across reps of: turns completed, CPU ms/turn (wait4),
CPU ms/turn (ps-tree), and — for reference — wall-gap ms/turn.

CAVEAT: the instant mock returns canned tool-calls, never real text, so some
agents misbehave (e.g. opencode has quit early at ~17 turns). CPU/turn is only
as trustworthy as the scenario; the `turns` column shows who bailed, and a run
that stops early divides a shorter CPU total by fewer turns (still per-turn, but
on a truncated loop). For a real-task memory comparison use realoverhead.py.
"""
import argparse, fcntl, importlib.util, json, os, pty, re, shutil, statistics, subprocess, sys, tempfile, termios, threading, time
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


def parse_cpu(s):
    """`ps -o time=` → seconds. Forms: MM:SS.ss, H:MM:SS, SS.ss."""
    s = s.strip()
    if not s:
        return 0.0
    parts = s.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except ValueError:
        return 0.0


def sample_tree_cpu(root, seen):
    """Record each tree pid's cumulative CPU into `seen` (keep the max). Returns
    the tree's current total RSS in KB (for peak-memory tracking)."""
    try:
        out = subprocess.check_output(["ps", "-o", "pid=,ppid=,time=,rss=", "-A"], text=True)
    except Exception:
        return 0
    kids, cpu, rss = defaultdict(list), {}, {}
    for ln in out.splitlines():
        q = ln.split(None, 3)
        if len(q) < 4:
            continue
        try:
            pid_, pp_ = int(q[0]), int(q[1])
            rss[pid_] = int(q[3])
        except ValueError:
            continue
        kids[pp_].append(pid_)
        cpu[pid_] = parse_cpu(q[2])
    st, total_rss = [root], 0
    while st:
        x = st.pop()
        if x in cpu:
            seen[x] = max(seen.get(x, 0.0), cpu[x])
            total_rss += rss.get(x, 0)
        st += kids.get(x, [])
    return total_rss


def wait_rusage(p, timeout):
    """Reap `p` with wait4 and return its user+sys CPU seconds, covering the
    agent and every child it reaped. Killed after `timeout` seconds, and still
    measured."""
    deadline = time.time() + timeout
    while True:
        pid, status, ru = os.wait4(p.pid, os.WNOHANG)
        if pid:
            p.returncode = os.waitstatus_to_exitcode(status)
            return ru.ru_utime + ru.ru_stime
        if time.time() > deadline:
            p.kill()
            deadline = float("inf")
        time.sleep(0.005)

def path_without(path, exe, shims):
    """PATH with `exe` hidden. A directory holding it is swapped for a shim
    directory of links to everything else in it, rather than dropped: on Linux
    tmux lives in /usr/bin, and dropping that would hide bash too."""
    out = []
    for i, d in enumerate(path.split(os.pathsep)):
        if not d or not os.access(os.path.join(d, exe), os.X_OK):
            out.append(d)
            continue
        shim = shims / str(i)
        if not shim.is_dir():
            shim.mkdir(parents=True)
            for e in os.scandir(d):
                if e.name != exe:
                    os.symlink(e.path, shim / e.name)
        out.append(str(shim))
    return os.pathsep.join(d for d in out if d)


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
    stdin_data = None
    if agent == "aider":
        # aider has no tool-call loop; drive its stdin REPL instead, where each
        # line is one model request, so it makes `turns` requests like the rest.
        # It is an edit-block agent, so this is per-MESSAGE overhead (marked * in
        # the report), not the same tool-loop turn as the others.
        v1 = f"{run.API}/v1"
        cmd = [run.agent_exe("aider"), "--model", "openai/fake", "--yes-always", "--no-auto-commits",
               "--no-check-update", "--no-show-model-warnings", "--no-pretty",
               "--no-stream", "--no-gitignore", "--no-analytics"]
        extra = {"OPENAI_API_BASE": v1, "OPENAI_API_KEY": run.API_KEY, "AIDER_HOME": str(home / "aiderhome")}
        subprocess.run(["git", "init", "-q"], cwd=wd)
        stdin_data = "".join(f"read file f{i}.txt\n" for i in range(turns)) + "/exit\n"
    else:
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
    if agent == "openhands":
        # With tmux on PATH, OpenHands runs its shell in a tmux server that
        # detaches from the process tree, so neither wait4 nor the ps-tree
        # poll would see that CPU. Without it, OpenHands runs commands as plain
        # child processes, like every other agent here, and all of it counts.
        env["PATH"] = path_without(env.get("PATH", ""), "tmux", home / "path-without-tmux")
    # CPU comes from wait4 on the agent itself (see wait_rusage), so nothing
    # wraps it.
    tcmd = list(cmd)
    errf = home / f"{agent}.stderr"
    # forge uses rustyline, which opens /dev/tty and fails ("Device not
    # configured") without a controlling terminal, so give it a PTY that is one
    # (setsid + TIOCSCTTY) and drain the master, or it blocks.
    use_pty = agent == "forge"
    mfd = sfd = None
    if use_pty:
        env["TERM"] = "xterm-256color"
        mfd, sfd = pty.openpty()
    with open(errf, "w") as ef:
        if use_pty:
            def _ctty():
                os.setsid()
                fcntl.ioctl(sfd, termios.TIOCSCTTY, 0)
            p = subprocess.Popen(tcmd, cwd=wd, env=env, stdin=sfd, stdout=sfd,
                                 stderr=ef, preexec_fn=_ctty)
            os.close(sfd)

            def _drain():
                while True:
                    try:
                        if not os.read(mfd, 65536):
                            break
                    except OSError:
                        break
            threading.Thread(target=_drain, daemon=True).start()
        else:
            p = subprocess.Popen(tcmd, cwd=wd, env=env, stdout=subprocess.DEVNULL, stderr=ef,
                                 stdin=(subprocess.PIPE if stdin_data else subprocess.DEVNULL))
            if stdin_data:
                try:
                    p.stdin.write(stdin_data.encode())
                    p.stdin.close()
                except Exception:
                    pass
        seen = {}
        peak_rss = [0]

        done = threading.Event()

        def poll():
            # Not p.poll(): reaping the agent here would lose its rusage.
            while not done.is_set():
                r = sample_tree_cpu(p.pid, seen)
                if r > peak_rss[0]:
                    peak_rss[0] = r
                time.sleep(0.06)

        th = threading.Thread(target=poll)
        th.start()
        cpu_time = wait_rusage(p, 240)
        done.set()
        th.join()
    if mfd is not None:
        try:
            os.close(mfd)
        except OSError:
            pass
    mock.kill()

    ts = [json.loads(l)["t"] for l in log.read_text().splitlines() if l.strip()]
    nturns = len(ts)
    if nturns < 2:
        return {"turns": nturns, "cpu_time": None, "cpu_tree": None, "wall": None}
    gaps = [(ts[i + 1] - ts[i]) * 1000 for i in range(len(ts) - 1)]
    cpu_tree = sum(seen.values())
    return {
        "turns": nturns,
        "cpu_time": (cpu_time * 1000 / nturns) if cpu_time is not None else None,
        "cpu_tree": (cpu_tree * 1000 / nturns) if cpu_tree else None,
        "wall": statistics.median(gaps),
        "rss": (peak_rss[0] / 1024) if peak_rss[0] else None,  # peak tree RSS, MB
    }


def agg(vals):
    """median; mean±sd (CV%) across reps — the spread shows significance."""
    vals = [v for v in vals if v is not None]
    if not vals:
        return "n/a"
    med = statistics.median(vals)
    mean = statistics.mean(vals)
    sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
    cv = (sd / mean * 100) if mean else 0.0
    return f"{med:6.1f} | {mean:6.1f}±{sd:4.1f} ({cv:3.0f}%)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agents", nargs="*",
                    default=["chanto", "opencode", "goose", "codex", "claude", "aider"])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--turns", type=int, default=40)
    ap.add_argument("--blob-kb", type=int, default=50)
    a = ap.parse_args()
    home = Path(tempfile.mkdtemp(prefix="cputurn-"))
    (home / "work").mkdir()
    run.WORK = home / "work"
    run.API_KEY = "x"
    print(f"CPU/turn: {a.turns} turns, {a.blob_kb} KB/turn, {a.reps} reps (model instant, CPU excl. model)\n")
    hdr = f"{'agent':10} {'turns':>6} {'reps':>4}  {'CPU ms/turn (wait4)':>30}  {'peak RSS MB':>22}"
    print(hdr)
    print("-" * len(hdr))
    for agent in a.agents:
        runs = [r for r in (one_run(agent, home, a.turns, a.blob_kb) for _ in range(a.reps)) if r]
        if not runs:
            print(f"{agent:10} {'—':>6}  did not run")
            continue
        t = statistics.median(r["turns"] for r in runs)
        print(f"{agent:10} {t:6.0f} {len(runs):4d}  {agg([r['cpu_time'] for r in runs]):>30}  "
              f"{agg([r['rss'] for r in runs]):>22}", flush=True)
    print("\nEach cell: median | mean±sd (CV%). Low CV% + separated means = a real difference.")
    print("peak RSS = max process-tree resident set over the run (sampled every 60 ms).")
    print("turns = model requests the agent made (short = it quit early vs the mock).")
    shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    main()
