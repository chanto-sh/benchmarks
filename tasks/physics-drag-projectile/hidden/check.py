import math
import sys

sys.path.insert(0, ".")
from projectile import flight  # the code under test


def reference(v0, ang, m, k, g, h0):
    """RK4 at a fine step, events located by re-stepping with bisection on the step length."""
    def f(s):
        sp = math.hypot(s[2], s[3])
        return (s[2], s[3], -k / m * sp * s[2], -g - k / m * sp * s[3])

    def step(s, h):
        a = f(s)
        b = f([x + h / 2 * y for x, y in zip(s, a)])
        c = f([x + h / 2 * y for x, y in zip(s, b)])
        d = f([x + h * y for x, y in zip(s, c)])
        return [x + h / 6 * (p + 2 * q + 2 * r + w) for x, p, q, r, w in zip(s, a, b, c, d)]

    def root(s, h, i):
        lo, hi = 0.0, h
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if step(s, mid)[i] > 0 else (lo, mid)
        return lo

    th = math.radians(ang)
    s = [0.0, h0, v0 * math.cos(th), v0 * math.sin(th)]
    t, apex, h = 0.0, h0, 2.5e-4
    while True:
        n = step(s, h)
        if s[3] > 0 >= n[3]:
            apex = max(apex, step(s, root(s, h, 3))[1])
        if n[1] <= 0 and n[3] < 0:
            r = root(s, h, 1)
            return {"range": step(s, r)[0], "apex": apex, "time": t + r}
        s, t = n, t + h


cases = [
    # v0, angle, mass, k, g, h0
    (55.0, 38.0, 0.43, 0.0021, 9.81, 0.0),
    (120.0, 60.0, 2.5, 0.004, 9.81, 0.0),
    (30.0, 15.0, 0.145, 0.0013, 9.81, 1.8),
    (80.0, 70.0, 5.0, 0.02, 9.81, 25.0),
    (40.0, 45.0, 1.0, 0.003, 1.62, 0.0),
    (12.0, 5.0, 0.05, 0.0004, 9.81, 3.0),
]
fail = []
for c in cases:
    want = reference(*c)
    v0, ang, m, k, g, h0 = c
    got = flight(v0, ang, m, k, g=g, h0=h0)
    for key in ("range", "apex", "time"):
        rel = abs(got[key] - want[key]) / abs(want[key])
        if rel > 1e-4:
            fail.append(f"flight{c}: {key} = {got[key]:.6g}, expected {want[key]:.6g} (rel err {rel:.1e})")
if fail:
    print("\n".join(fail))
    sys.exit(1)
print("hidden ok")
