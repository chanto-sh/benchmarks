"""1D chain of masses between two fixed walls, joined by FPU-beta springs.

x[i] is the displacement of mass i from its rest position. The spring between
neighbours (and between the end masses and the walls, which never move) with
stretch d stores k d^2 / 2 + beta d^4 / 4 and pulls with force k d + beta d^3.
"""


def forces(x, k, beta):
    n = len(x)
    ext = [0.0] + list(x) + [0.0]  # walls at both ends
    f = [0.0] * n
    for s in range(n + 1):  # spring s joins ext[s] and ext[s + 1]
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


def simulate(x0, v0, masses, k, beta, dt, steps):
    """Velocity Verlet; returns (x, v) after `steps` steps."""
    x, v = list(x0), list(v0)
    m = masses[0]
    for _ in range(steps):
        a = [f / m for f in forces(x, k, beta)]
        x = [xi + vi * dt + 0.5 * ai * dt * dt for xi, vi, ai in zip(x, v, a)]
        v = [vi + ai * dt for vi, ai in zip(v, a)]
    return x, v
