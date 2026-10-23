"""1D heat equation u_t = alpha u_xx on a rod, explicit finite differences."""
import math


def solve(u0, alpha, length, t_end):
    """Temperature profile at time t_end.

    u0: initial temperatures at nx equally spaced points from 0 to length
        (both ends included; the end values are held fixed).
    """
    nx = len(u0)
    u = list(u0)
    if t_end <= 0 or alpha == 0 or nx < 3:
        return u
    dx = length / (nx - 1)
    # FTCS is stable for r = alpha dt / dx^2 <= 1/2; stay well inside and
    # use a whole number of equal steps so the last one lands on t_end.
    dt_max = 0.4 * dx * dx / alpha
    steps = max(1, math.ceil(t_end / dt_max))
    r = alpha * (t_end / steps) / (dx * dx)
    for _ in range(steps):
        u = [u[0]] + [u[i] + r * (u[i - 1] - 2 * u[i] + u[i + 1]) for i in range(1, nx - 1)] + [u[-1]]
    return u
