"""Orbit measurements for a test particle in a central force field."""
import math


def newtonian(gm):
    def accel(x, y):
        r3 = (x * x + y * y) ** 1.5
        return -gm * x / r3, -gm * y / r3
    return accel


def radial_period(r0, v0, accel):
    """Kepler's third law: recover GM from the force at r0, a from vis-viva."""
    r = math.hypot(*r0)
    ax, ay = accel(*r0)
    gm = math.hypot(ax, ay) * r * r
    v2 = v0[0] ** 2 + v0[1] ** 2
    a = 1 / (2 / r - v2 / gm)
    return 2 * math.pi * math.sqrt(a ** 3 / gm)
