"""Point-mass projectile with quadratic air drag."""
import math


def _deriv(s, mass, k, g):
    x, y, vx, vy = s
    sp = math.hypot(vx, vy)
    return (vx, vy, -k / mass * sp * vx, -g - k / mass * sp * vy)


def _rk4(s, h, mass, k, g):
    k1 = _deriv(s, mass, k, g)
    k2 = _deriv([a + h / 2 * b for a, b in zip(s, k1)], mass, k, g)
    k3 = _deriv([a + h / 2 * b for a, b in zip(s, k2)], mass, k, g)
    k4 = _deriv([a + h * b for a, b in zip(s, k3)], mass, k, g)
    return [a + h / 6 * (b + 2 * c + 2 * d + e) for a, b, c, d, e in zip(s, k1, k2, k3, k4)]


def _refine(s, h, idx, mass, k, g):
    """Sub-step length in (0, h] where component idx of the state reaches 0 (bisection)."""
    lo, hi = 0.0, h
    for _ in range(60):
        mid = (lo + hi) / 2
        if _rk4(s, mid, mass, k, g)[idx] > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def flight(v0, angle_deg, mass, k, g=9.81, h0=0.0):
    """Return {"range": metres, "apex": metres, "time": seconds}."""
    th = math.radians(angle_deg)
    s = [0.0, float(h0), v0 * math.cos(th), v0 * math.sin(th)]
    t = 0.0
    apex = float(h0)
    dt = 1e-3
    while True:
        n = _rk4(s, dt, mass, k, g)
        if s[3] > 0 >= n[3]:
            h = _refine(s, dt, 3, mass, k, g)
            apex = max(apex, _rk4(s, h, mass, k, g)[1])
        if n[1] <= 0 and n[3] < 0:
            h = _refine(s, dt, 1, mass, k, g)
            last = _rk4(s, h, mass, k, g)
            return {"range": last[0], "apex": apex, "time": t + h}
        s, t = n, t + dt
