"""Point-mass projectile with linear air drag (closed form)."""
import math


def flight(v0, angle_deg, mass, k, g=9.81, h0=0.0):
    th = math.radians(angle_deg)
    vx0, vy0 = v0 * math.cos(th), v0 * math.sin(th)
    if k == 0:
        t = (vy0 + math.sqrt(vy0 * vy0 + 2 * g * h0)) / g
        return {"range": vx0 * t, "apex": h0 + vy0 * vy0 / (2 * g), "time": t}
    b = k / mass
    vt = g / b

    def y(t):
        return h0 + (vy0 + vt) / b * (1 - math.exp(-b * t)) - vt * t

    lo, hi = 1e-9, 1.0
    while y(hi) > 0:
        hi *= 2
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if y(mid) > 0 else (lo, mid)
    tp = math.log(1 + vy0 / vt) / b
    return {"range": vx0 / b * (1 - math.exp(-b * lo)), "apex": y(tp), "time": lo}
