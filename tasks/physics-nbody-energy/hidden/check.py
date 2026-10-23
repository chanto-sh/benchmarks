import math
import sys

sys.path.insert(0, ".")
from nbody import simulate  # the code under test


def acc(m, p, G):
    n = len(m)
    a = [[0.0, 0.0] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                dx = p[j][0] - p[i][0]
                dy = p[j][1] - p[i][1]
                r3 = (dx * dx + dy * dy) ** 1.5
                a[i][0] += G * m[j] * dx / r3
                a[i][1] += G * m[j] * dy / r3
    return a


def energy(m, p, v, G):
    e = sum(0.5 * mi * (vi[0] ** 2 + vi[1] ** 2) for mi, vi in zip(m, v))
    for i in range(len(m)):
        for j in range(i + 1, len(m)):
            e -= G * m[i] * m[j] / math.hypot(p[j][0] - p[i][0], p[j][1] - p[i][1])
    return e


def rk4(m, p, v, dt, steps, G):
    n = len(m)

    def f(s):
        a = acc(m, [s[2 * i] for i in range(n)], G)
        out = []
        for i in range(n):
            out += [s[2 * i + 1], a[i]]
        return out

    def add(s, k, h):
        return [[s[i][0] + h * k[i][0], s[i][1] + h * k[i][1]] for i in range(len(s))]

    s = []
    for i in range(n):
        s += [list(p[i]), list(v[i])]
    for _ in range(steps):
        k1 = f(s)
        k2 = f(add(s, k1, dt / 2))
        k3 = f(add(s, k2, dt / 2))
        k4 = f(add(s, k3, dt))
        s = [[s[i][c] + dt / 6 * (k1[i][c] + 2 * k2[i][c] + 2 * k3[i][c] + k4[i][c]) for c in (0, 1)]
             for i in range(len(s))]
    return [s[2 * i] for i in range(n)], [s[2 * i + 1] for i in range(n)]


def mom(m, v):
    return [sum(mi * vi[c] for mi, vi in zip(m, v)) for c in (0, 1)]


fail = []
# Hidden system: a star and two planets on eccentric orbits, G != 1, drifting frame.
G = 2.5
m = [10.0, 0.03, 0.01]
p = [[0.0, 0.0], [1.3, 0.0], [0.0, -2.2]]
v = [[0.01, 0.02], [0.0, math.sqrt(G * 10 / 1.3) * 1.15], [math.sqrt(G * 10 / 2.2) * 0.9, 0.02]]
e0 = energy(m, p, v, G)
m0 = mom(m, v)
P, V = simulate(m, [list(x) for x in p], [list(x) for x in v], 0.002, 30000, G=G)
drift = abs(energy(m, P, V, G) - e0) / abs(e0)
print(f"relative energy drift over 30000 steps: {drift:.2e}")
if drift > 2e-5:
    fail.append(f"energy drifted by {drift:.2e} (limit 2e-5)")
m1 = mom(m, V)
if max(abs(a - b) for a, b in zip(m0, m1)) > 1e-9:
    fail.append(f"momentum not conserved: {m0} -> {m1}")
# Short-time accuracy against a fine RK4 reference: it has to integrate this system.
pin = [list(x) for x in p]
P2, V2 = simulate(m, pin, [list(x) for x in v], 0.002, 1000, G=G)
Pr, Vr = rk4(m, p, v, 0.0005, 4000, G)
err = max(math.hypot(P2[i][0] - Pr[i][0], P2[i][1] - Pr[i][1]) for i in range(3))
print(f"position error vs reference at t=2: {err:.2e}")
if err > 1e-3:
    fail.append(f"trajectory differs from reference by {err:.2e}")
if pin != p:
    fail.append("simulate mutated its input positions")
if fail:
    print("\n".join(fail))
    sys.exit(1)
print("hidden ok")
