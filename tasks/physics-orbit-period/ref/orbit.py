"""Orbit measurements for a test particle in a central force field."""
import math


def newtonian(gm):
    """Inverse-square attraction toward the origin."""
    def accel(x, y):
        r3 = (x * x + y * y) ** 1.5
        return -gm * x / r3, -gm * y / r3
    return accel


def _rk4(s, h, accel):
    def f(s):
        ax, ay = accel(s[0], s[1])
        return (s[2], s[3], ax, ay)
    k1 = f(s)
    k2 = f([a + h / 2 * b for a, b in zip(s, k1)])
    k3 = f([a + h / 2 * b for a, b in zip(s, k2)])
    k4 = f([a + h * b for a, b in zip(s, k3)])
    return [a + h / 6 * (b + 2 * c + 2 * d + e) for a, b, c, d, e in zip(s, k1, k2, k3, k4)]


def _rdot(s):
    return s[0] * s[2] + s[1] * s[3]  # sign of dr/dt


def radial_period(r0, v0, accel, max_steps=2_000_000):
    """Time between two successive closest approaches to the origin.

    RK4 with a step scaled to the local dynamical time; a closest approach is
    where r.v changes sign from negative to positive, located by bisecting
    the length of the step that crosses it.
    """
    s = [float(r0[0]), float(r0[1]), float(v0[0]), float(v0[1])]
    t = 0.0
    passes = []
    for _ in range(max_steps):
        r = math.hypot(s[0], s[1])
        ax, ay = accel(s[0], s[1])
        h = 0.002 * min(r / max(math.hypot(s[2], s[3]), 1e-300), math.sqrt(r / max(math.hypot(ax, ay), 1e-300)))
        n = _rk4(s, h, accel)
        if _rdot(s) < 0 <= _rdot(n):
            lo, hi = 0.0, h
            for _ in range(60):
                mid = (lo + hi) / 2
                if _rdot(_rk4(s, mid, accel)) < 0:
                    lo = mid
                else:
                    hi = mid
            passes.append(t + (lo + hi) / 2)
            if len(passes) == 2:
                return passes[1] - passes[0]
        s, t = n, t + h
    raise RuntimeError("no two closest approaches found (circular or unbound orbit?)")
