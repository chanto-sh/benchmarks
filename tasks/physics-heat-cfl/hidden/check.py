import math
import sys

sys.path.insert(0, ".")
from heat import solve  # the code under test


def fine(u0, alpha, length, t_end, r=0.1):
    """Reference: FTCS at a small mesh ratio, landing exactly on t_end."""
    nx = len(u0)
    dx = length / (nx - 1)
    steps = max(1, math.ceil(t_end / (r * dx * dx / alpha)))
    rr = alpha * (t_end / steps) / (dx * dx)
    u = list(u0)
    for _ in range(steps):
        u = [u[0]] + [u[i] + rr * (u[i - 1] - 2 * u[i] + u[i + 1]) for i in range(1, nx - 1)] + [u[-1]]
    return u


def sine(nx, amp=1.0):
    return [amp * math.sin(math.pi * i / (nx - 1)) for i in range(nx)]


fail = []


def expect(label, got, want, tol):
    if len(got) != len(want):
        fail.append(f"{label}: returned {len(got)} points, expected {len(want)}")
        return
    err = max(abs(a - b) if a == a else float("inf") for a, b in zip(got, want))
    if not err <= tol:
        fail.append(f"{label}: max error {err:.3g} (tolerance {tol:g})")


# 1. fine grid, high diffusivity: a fixed or loosely chosen dt goes unstable
nx, a, t = 201, 2.0, 0.01
expect("fine grid, alpha=2", solve(sine(nx), a, 1.0, t),
       [math.exp(-a * math.pi ** 2 * t) * s for s in sine(nx)], 1e-3)
# 2. very slow rod and an end time that is not a multiple of a stable step
nx, a, t = 11, 0.001, 7.3
expect("coarse grid, t_end=7.3", solve(sine(nx), a, 1.0, t),
       [math.exp(-a * math.pi ** 2 * t) * s for s in sine(nx)], 2e-3)
# 3. a hot spot on a 2.5 m rod with different fixed end temperatures
nx = 41
u0 = [1.0] + [max(0.0, 1 - abs(i - 15) / 6) * 4.0 for i in range(1, nx - 1)] + [0.0]
got = solve(u0, 0.3, 2.5, 0.35)
expect("hot spot, mixed ends", got, fine(u0, 0.3, 2.5, 0.35), 5e-3)
if got and max(got) > max(u0) + 1e-9:
    fail.append("hot spot: temperature rose above the initial maximum (unstable)")
# 4. long run: must relax to the straight line between the end temperatures
nx = 21
u0 = [3.0] + [0.0] * (nx - 2) + [-1.0]
expect("steady state", solve(u0, 0.5, 1.0, 40.0), [3.0 - 4.0 * i / (nx - 1) for i in range(nx)], 1e-6)
# 5. short rod, very conductive, tiny end time
nx, a, t, L = 31, 5.0, 0.0007, 0.2
expect("short rod", solve(sine(nx, 2.0), a, L, t),
       [math.exp(-a * (math.pi / L) ** 2 * t) * s for s in sine(nx, 2.0)], 2e-3 * 2)
if fail:
    print("\n".join(fail))
    sys.exit(1)
print("hidden ok")
