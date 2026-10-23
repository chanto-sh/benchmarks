"""Orbit measurements for a test particle in a central force field."""


def newtonian(gm):
    """Inverse-square attraction toward the origin."""
    def accel(x, y):
        r3 = (x * x + y * y) ** 1.5
        return -gm * x / r3, -gm * y / r3
    return accel


def radial_period(r0, v0, accel):
    """Time between two successive closest approaches to the origin."""
    raise NotImplementedError
