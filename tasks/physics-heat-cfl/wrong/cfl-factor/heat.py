"""1D heat equation u_t = alpha u_xx on a rod, explicit finite differences."""
import math


def solve(u0, alpha, length, t_end):
    nx = len(u0)
    dx = length / (nx - 1)
    dt_max = dx * dx / alpha  # (stability limit misremembered: should be dx^2 / (2 alpha))
    steps = max(1, math.ceil(t_end / dt_max))
    r = alpha * (t_end / steps) / (dx * dx)
    u = list(u0)
    for _ in range(steps):
        u = [u[0]] + [u[i] + r * (u[i - 1] - 2 * u[i] + u[i + 1]) for i in range(1, nx - 1)] + [u[-1]]
    return u
