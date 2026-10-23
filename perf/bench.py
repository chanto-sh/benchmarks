"""Time Chanto end to end against the instant mock (mock.py).

usage: bench.py <binary> [label] [runs]
"""
import os, resource, shutil, statistics, subprocess, sys, tempfile, time

BIN = sys.argv[1]
LABEL = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(BIN)
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 7
HERE = os.path.dirname(os.path.abspath(__file__))
PORTS = {"short": 4301, "long": 4302, "tools": 4303}

work = tempfile.mkdtemp(prefix="hperf-")
proj = os.path.join(work, "proj")
os.makedirs(proj)
with open(os.path.join(proj, "big.txt"), "w") as f:
    for i in range(400000):
        f.write(f"line {i} some text here\n")
subprocess.run(["git", "init", "-q"], cwd=proj)


def env(home, mode=None, real_home=False):
    e = {"PATH": os.environ["PATH"], "HOME": os.environ["HOME"], "TERM": "xterm-256color",
         "CHANTO_API_KEY": "x", "OPENAI_API_KEY": "x"}
    if not real_home:
        e["CHANTO_HOME"] = home
        e["CHANTO_COMPAT_HOME"] = os.path.join(home, "compat")
    if mode == "tools":
        e["MOCK_FILE"] = os.path.join(proj, "big.txt")
    return e


def run(args, e, cwd=proj):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    t = time.perf_counter()
    p = subprocess.run(args, cwd=cwd, env=e, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    wall = time.perf_counter() - t
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)
    if p.returncode != 0:
        print("  FAILED:", (p.stderr or p.stdout)[-400:], file=sys.stderr)
    return wall, cpu, after.ru_maxrss


def base(mode):
    return [BIN, "--provider", "openai", "--base-url", f"http://127.0.0.1:{PORTS[mode]}/v1", "--model", "mock",
            "--mode", "bypassPermissions"]


def scenario(name, args_fn, mode, real_home=False, setup=None):
    walls, cpus = [], []
    for i in range(RUNS):
        home = tempfile.mkdtemp(prefix="hhome-")
        if setup:
            setup(home)
        if mode == "tools":
            # restore the edited file
            subprocess.run(["git", "checkout", "-q", "--", "."], cwd=proj)
        w, c, _ = run(args_fn(home), env(home, mode, real_home))
        walls.append(w); cpus.append(c)
        shutil.rmtree(home, ignore_errors=True)
    w, c = statistics.median(walls[1:]), statistics.median(cpus[1:])
    print(f"{LABEL:14} {name:22} wall {w*1000:8.0f} ms   cpu {c*1000:8.0f} ms")
    return w, c


subprocess.run(["git", "add", "-A"], cwd=proj); subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=a", "commit", "-qm", "i"], cwd=proj)

scenario("startup (empty home)", lambda h: base("short") + ["-p", "hi"], "short")
scenario("startup (real config)", lambda h: base("short") + ["-p", "hi"], "short", real_home=True)
scenario("stream 30k tokens", lambda h: base("long") + ["-p", "write a long doc"], "long")
scenario("Read/Grep/Edit 9MB", lambda h: base("tools") + ["-p", "edit it"], "tools")


def long_session(home):
    # Six turns, each adding a 30k-token answer, to make a large session.
    e = env(home, "long")
    for i in range(6):
        subprocess.run(base("long") + (["-c"] if i else []) + ["-p", f"turn {i}"], cwd=proj, env=e,
                       stdin=subprocess.DEVNULL, capture_output=True, timeout=300)


scenario("turn on 180k-token session", lambda h: base("short") + ["-c", "-p", "one more"], "short", setup=long_session)
shutil.rmtree(work, ignore_errors=True)
