"""2D Ising model, Metropolis single-spin-flip dynamics.

E = -J * sum_<ij> s_i s_j - h * sum_i s_i on an L x L periodic lattice.
spins is a list of L lists of +1/-1.
"""
import math
import random


def energy(spins, J=1.0, h=0.0):
    L = len(spins)
    e = 0.0
    for i in range(L):
        for j in range(L):
            s = spins[i][j]
            e -= J * s * (spins[(i + 1) % L][j] + spins[i][(j + 1) % L])
            e -= h * s
    return e


def magnetization(spins):
    L = len(spins)
    return sum(map(sum, spins)) / (L * L)


def delta_energy(spins, i, j, J=1.0, h=0.0):
    """Energy change if spin (i, j) is flipped."""
    L = len(spins)
    s = spins[i][j]
    nb = spins[(i + 1) % L][j] + spins[(i - 1) % L][j] + spins[i][(j + 1) % L] + spins[i][(j - 1) % L]
    return 2 * s * J * nb


def accept(dE, T, u):
    """Metropolis rule: accept a move with energy change dE at temperature T given u ~ U[0, 1)."""
    return dE <= 0 or u < math.exp(-dE / T)


def sweep(spins, T, rng, J=1.0, h=0.0):
    """One Metropolis sweep in row-major order, in place.

    Exactly one rng.random() is drawn per site, whether or not it is needed,
    so a given seed always produces the same run.
    """
    L = len(spins)
    for i in range(L):
        for j in range(L):
            u = rng.random()
            if accept(delta_energy(spins, i, j, J, h), T, u):
                spins[i][j] = -spins[i][j]


def run(L, T, sweeps, seed=0, J=1.0, h=0.0, start="up"):
    rng = random.Random(seed)
    if start == "up":
        spins = [[1] * L for _ in range(L)]
    else:
        spins = [[rng.choice((-1, 1)) for _ in range(L)] for _ in range(L)]
    for _ in range(sweeps):
        sweep(spins, T, rng, J, h)
    return spins
