"""Hidden check: exact agreement with the original semantics, then speed."""
import importlib.util
import json
import random
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HIDDEN = sys.argv[1]
spec = importlib.util.spec_from_file_location("oracle", HIDDEN + "/oracle.py")
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)
sys.path.insert(0, ".")
import sessions  # noqa: E402  (the agent's module, from the workspace)


def norm(ss):
    return [(s["user"], s["start"], s["end"], list(s["pages"])) for s in ss]


def small_cases():
    rng = random.Random(7)
    for case in range(300):
        users = [f"u{i}" for i in range(rng.randint(1, 4))]
        n = rng.randint(0, 25)
        ev = [(rng.choice(users), rng.choice([0, 10, 20, 30, 40, 1800, 1810, 3600, 3610]) + rng.randint(0, 2) * 1800,
               rng.choice(["/z", "/a", "/m", "/b"])) for _ in range(n)]
        gap = rng.choice([1800, 10, 0, 1810])
        yield ev, gap
    # exact-boundary and tie cases
    yield [("x", 0, "/z"), ("x", 1800, "/a"), ("x", 3601, "/b")], 1800
    yield [("x", 5, "/z"), ("x", 5, "/a"), ("y", 5, "/c"), ("x", 4, "/q")], 1800


for ev, gap in small_cases():
    want = norm(oracle.sessionize(list(ev), gap))
    got = norm(sessions.sessionize(list(ev), gap))
    if got != want:
        sys.exit(f"sessionize differs on {ev!r} gap={gap}:\n got  {got}\n want {want}")
    os_ = oracle.sessionize(list(ev), gap)
    if list(sessions.top_landing_pages(os_, 3)) != oracle.top_landing_pages(os_, 3):
        sys.exit(f"top_landing_pages differs on {ev!r}")
    if abs(sessions.bounce_rate(os_) - oracle.bounce_rate(os_)) > 1e-12:
        sys.exit("bounce_rate differs")
print("semantics ok")

# Speed: a big hidden day of traffic, in a child process with a hard deadline.
child = r"""
import json, random, sys, time
sys.path.insert(0, ".")
import sessions
rng = random.Random(20261015)
pages = ["/", "/pricing", "/docs", "/blog", "/signup", "/login"] + [f"/p/{i}" for i in range(300)]
ev = [(f"user{rng.randrange(3000)}", rng.randrange(86400), rng.choice(pages)) for _ in range(250000)]
t = time.time()
s = sessions.sessionize(ev)
top = sessions.top_landing_pages(s, 5)
br = sessions.bounce_rate(s)
el = time.time() - t
print(json.dumps({"n": len(s), "pages": sum(len(x["pages"]) for x in s), "top": top, "br": round(br, 9),
                  "first": [s[0]["user"], s[0]["start"], s[0]["pages"][:3]], "secs": el}))
"""
t0 = time.time()
try:
    r = subprocess.run([sys.executable, "-c", child], capture_output=True, text=True, timeout=30)
except subprocess.TimeoutExpired:
    sys.exit("too slow: 250k events did not finish within 30 s")
if r.returncode:
    sys.exit("big run failed:\n" + r.stderr[-1500:])
got = json.loads(r.stdout)
exp = json.load(open(HIDDEN + "/big_expected.json"))
for k in ("n", "pages", "top", "br", "first"):
    if json.loads(json.dumps(got[k])) != exp[k]:
        sys.exit(f"big run: {k} = {got[k]!r}, expected {exp[k]!r}")
if got["secs"] > 15:
    sys.exit(f"too slow: {got['secs']:.1f}s for 250k events")
print(f"perf ok ({got['secs']:.2f}s)")
