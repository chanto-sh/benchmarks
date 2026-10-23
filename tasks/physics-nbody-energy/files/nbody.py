"""Small 2D gravitational N-body integrator."""
import math


def accelerations(masses, positions, G=1.0):
    n = len(masses)
    acc = [[0.0, 0.0] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            dx = positions[j][0] - positions[i][0]
            dy = positions[j][1] - positions[i][1]
            r3 = (dx * dx + dy * dy) ** 1.5
            acc[i][0] += G * masses[j] * dx / r3
            acc[i][1] += G * masses[j] * dy / r3
    return acc


def energy(masses, positions, velocities, G=1.0):
    n = len(masses)
    ke = sum(0.5 * m * (v[0] ** 2 + v[1] ** 2) for m, v in zip(masses, velocities))
    pe = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            r = math.hypot(positions[j][0] - positions[i][0], positions[j][1] - positions[i][1])
            pe -= G * masses[i] * masses[j] / r
    return ke + pe


def simulate(masses, positions, velocities, dt, steps, G=1.0):
    """Advance the system `steps` steps of size `dt`; return (positions, velocities)."""
    raise NotImplementedError
