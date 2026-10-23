import math
import sys
import time

sys.path.insert(0, ".")
from orbit import radial_period  # the code under test


def quadrature_period(r0, v0, V):
    """Exact radial period of a central potential V(r): 2 * integral dr / sqrt(2 F(r))
    between the turning points, F = E - V - L^2 / (2 r^2), with r = c - d cos(theta)
    to remove the endpoint singularities (midpoint rule, spectrally accurate)."""
    r = math.hypot(*r0)
    L = r0[0] * v0[1] - r0[1] * v0[0]
    E = 0.5 * (v0[0] ** 2 + v0[1] ** 2) + V(r)
    F = lambda q: E - V(q) - L * L / (2 * q * q)  # noqa: E731

    def turning(step):
        a = r
        while True:
            b = a * step
            if F(b) < 0:
                break
            a = b
        for _ in range(200):
            m = (a + b) / 2
            a, b = (m, b) if F(m) > 0 else (a, m)
        return (a + b) / 2

    rmin, rmax = turning(0.999), turning(1.001)
    c, d = (rmax + rmin) / 2, (rmax - rmin) / 2
    n = 20000
    total = 0.0
    for i in range(n):
        th = math.pi * (i + 0.5) / n
        q = c - d * math.cos(th)
        total += d * math.sin(th) / math.sqrt(2 * max(F(q), 1e-300))
    return 2 * total * math.pi / n


def central(f):
    """accel(x, y) for a radial acceleration magnitude f(r) (positive = attractive)."""
    def accel(x, y):
        r = math.hypot(x, y)
        a = f(r)
        return -a * x / r, -a * y / r
    return accel


cases = []
# 1. very eccentric Kepler orbit, starting on the way in, GM != 1
gm, a_, e = 3.7, 2.0, 0.85
nu = 2.4  # true anomaly at the start
p = a_ * (1 - e * e)
rr = p / (1 + e * math.cos(nu))
pos = (rr * math.cos(nu), rr * math.sin(nu))
vr = math.sqrt(gm / p) * e * math.sin(nu)
vt = math.sqrt(gm / p) * (1 + e * math.cos(nu))
vel = (vr * math.cos(nu) - vt * math.sin(nu), vr * math.sin(nu) + vt * math.cos(nu))
cases.append(("eccentric Kepler, mid-orbit start", pos, (-vel[0], -vel[1]),
              central(lambda r: gm / r ** 2), 2 * math.pi * math.sqrt(a_ ** 3 / gm)))
# 2. inverse-square plus a 1/r^4 correction: the orbit precesses
beta = 0.05
cases.append(("precessing (1/r^4 correction)", (1.2, 0.3), (-0.2, 0.85),
              central(lambda r: (1 + beta / r ** 2) / r ** 2),
              quadrature_period((1.2, 0.3), (-0.2, 0.85), lambda r: -1 / r - beta / (3 * r ** 3))))
# 3. isotropic harmonic force: two closest approaches per revolution
k = 2.25
cases.append(("harmonic", (1.0, 0.4), (0.3, 1.2), central(lambda r: k * r), math.pi / math.sqrt(k)))
# 4. screened (Yukawa) potential V = -g exp(-r/lam) / r
g, lam = 2.0, 3.0
cases.append(("Yukawa", (0.0, -1.5), (0.9, 0.35),
              central(lambda r: g * math.exp(-r / lam) * (1 / r ** 2 + 1 / (lam * r))),
              quadrature_period((0.0, -1.5), (0.9, 0.35), lambda r: -g * math.exp(-r / lam) / r)))

fail = []
for label, pos, vel, acc, want in cases:
    t0 = time.time()
    try:
        got = radial_period(pos, vel, acc)
    except Exception as ex:  # noqa: BLE001
        fail.append(f"{label}: raised {ex!r}")
        continue
    rel = abs(got - want) / want
    print(f"{label}: {got:.9g} vs {want:.9g} (rel {rel:.1e}, {time.time() - t0:.2f}s)")
    if not rel <= 1e-6:
        fail.append(f"{label}: radial period {got!r}, expected {want!r}")
if fail:
    print("\n".join(fail))
    sys.exit(1)
print("hidden ok")
