"""Orbit measurements for a test particle in a central force field."""
import math


def newtonian(gm):
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


def radial_period(r0, v0, accel):
    """Time for the particle to sweep a full 2 pi around the origin."""
    s = [float(r0[0]), float(r0[1]), float(v0[0]), float(v0[1])]
    swept, t = 0.0, 0.0
    while True:
        r = math.hypot(s[0], s[1])
        h = 0.002 * r / math.hypot(s[2], s[3])
        n = _rk4(s, h, accel)
        d = math.atan2(s[0] * n[1] - s[1] * n[0], s[0] * n[0] + s[1] * n[1])
        if abs(swept + d) >= 2 * math.pi:
            frac = (2 * math.pi - abs(swept)) / abs(d)
            return t + frac * h
        swept += d
        s, t = n, t + h
