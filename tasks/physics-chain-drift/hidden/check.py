import math
import random
import sys

sys.path.insert(0, ".")
from chain import simulate  # the code under test


def forces(x, k, beta):
    n = len(x)
    ext = [0.0] + list(x) + [0.0]
    f = [0.0] * n
    for s in range(n + 1):
        d = ext[s + 1] - ext[s]
        t = k * d + beta * d ** 3
        if s > 0:
            f[s - 1] += t
        if s < n:
            f[s] -= t
    return f


def energy(x, v, masses, k, beta):
    ext = [0.0] + list(x) + [0.0]
    e = sum(0.5 * m * u * u for m, u in zip(masses, v))
    for s in range(len(x) + 1):
        d = ext[s + 1] - ext[s]
        e += 0.5 * k * d * d + 0.25 * beta * d ** 4
    return e


def rk4(x, v, masses, k, beta, dt, steps):
    n = len(x)
    s = list(x) + list(v)

    def f(s):
        return s[n:] + [fi / m for fi, m in zip(forces(s[:n], k, beta), masses)]

    for _ in range(steps):
        a = f(s)
        b = f([p + dt / 2 * q for p, q in zip(s, a)])
        c = f([p + dt / 2 * q for p, q in zip(s, b)])
        d = f([p + dt * q for p, q in zip(s, c)])
        s = [p + dt / 6 * (q + 2 * r + 2 * w + z) for p, q, r, w, z in zip(s, a, b, c, d)]
    return s[:n], s[n:]


rng = random.Random(7)
fail = []
n = 10
masses = [rng.uniform(0.5, 3.0) for _ in range(n)]
k, beta = 2.3, 1.7
x0 = [rng.uniform(-0.4, 0.4) for _ in range(n)]
v0 = [rng.uniform(-0.3, 0.3) for _ in range(n)]
e0 = energy(x0, v0, masses, k, beta)
x, v = simulate(x0, v0, masses, k, beta, 0.005, 30000)
drift = abs(energy(x, v, masses, k, beta) - e0) / e0
print(f"relative energy change over 30000 steps: {drift:.2e}")
if not drift < 1e-4:
    fail.append(f"energy not conserved for a chain with unequal masses ({drift:.2e})")
xs, vs = simulate(x0, v0, masses, k, beta, 0.005, 600)
xr, vr = rk4(x0, v0, masses, k, beta, 0.0025, 1200)
err = max(abs(a - b) for a, b in zip(xs + vs, xr + vr))
print(f"max state error vs reference at t=3: {err:.2e}")
if not err < 1e-3:
    fail.append(f"trajectory differs from the reference ({err:.2e})")
if fail:
    print("\n".join(fail))
    sys.exit(1)
print("hidden ok")
