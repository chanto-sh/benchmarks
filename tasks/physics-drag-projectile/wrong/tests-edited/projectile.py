"""Point-mass projectile with quadratic air drag (semi-implicit Euler, no event location)."""
import math


def flight(v0, angle_deg, mass, k, g=9.81, h0=0.0):
    th = math.radians(angle_deg)
    x, y, vx, vy = 0.0, float(h0), v0 * math.cos(th), v0 * math.sin(th)
    t, apex, dt = 0.0, float(h0), 1e-3
    while True:
        sp = math.hypot(vx, vy)
        vx += -k / mass * sp * vx * dt
        vy += (-g - k / mass * sp * vy) * dt
        x += vx * dt
        y += vy * dt
        t += dt
        apex = max(apex, y)
        if y <= 0 and vy < 0:
            return {"range": x, "apex": apex, "time": t}
