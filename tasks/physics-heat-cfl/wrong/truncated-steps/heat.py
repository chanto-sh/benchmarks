"""1D heat equation u_t = alpha u_xx on a rod, explicit finite differences."""


def solve(u0, alpha, length, t_end):
    nx = len(u0)
    dx = length / (nx - 1)
    dt = 0.45 * dx * dx / alpha
    steps = int(t_end / dt)
    u = list(u0)
    for _ in range(steps):
        r = alpha * dt / (dx * dx)
        u = [u[0]] + [u[i] + r * (u[i - 1] - 2 * u[i] + u[i + 1]) for i in range(1, nx - 1)] + [u[-1]]
    return u
