import math
import random
import sys

sys.path.insert(0, ".")
import ising  # the code under test


def ref_energy(s, J, h):
    L = len(s)
    return sum(-J * s[i][j] * (s[(i + 1) % L][j] + s[i][(j + 1) % L]) - h * s[i][j]
               for i in range(L) for j in range(L))


def ref_run(L, T, sweeps, seed, J, h):
    rng = random.Random(seed)
    s = [[rng.choice((-1, 1)) for _ in range(L)] for _ in range(L)]
    for _ in range(sweeps):
        for i in range(L):
            for j in range(L):
                u = rng.random()
                nb = s[(i + 1) % L][j] + s[(i - 1) % L][j] + s[i][(j + 1) % L] + s[i][(j - 1) % L]
                dE = 2 * s[i][j] * (J * nb + h)
                if dE <= 0 or u < math.exp(-dE / T):
                    s[i][j] = -s[i][j]
    return s


fail = []
rng = random.Random(2024)
# energy and delta_energy on rectangular-looking random states, with coupling and field
for L, J, h in [(6, 0.7, 0.3), (7, 1.3, -0.45), (3, 1.0, 0.0)]:
    s = [[rng.choice((-1, 1)) for _ in range(L)] for _ in range(L)]
    if abs(ising.energy(s, J, h) - ref_energy(s, J, h)) > 1e-9:
        fail.append(f"energy wrong for L={L}, J={J}, h={h}: {ising.energy(s, J, h)} vs {ref_energy(s, J, h)}")
    for _ in range(5):
        i, j = rng.randrange(L), rng.randrange(L)
        before = ref_energy(s, J, h)
        d = ising.delta_energy(s, i, j, J, h)
        s[i][j] *= -1
        if abs(ref_energy(s, J, h) - before - d) > 1e-9:
            fail.append(f"delta_energy wrong at ({i},{j}) for J={J}, h={h}")
            break
# the acceptance rule itself
for dE, T, u, want in [(-1.0, 2.0, 0.999, True), (0.0, 0.5, 0.999, True),
                       (2.0, 1.5, 0.26, True), (2.0, 1.5, 0.27, False),
                       (8.0, 4.0, 0.13, True), (8.0, 4.0, 0.14, False),
                       (4.0, 0.5, 1e-4, True), (4.0, 0.5, 4e-4, False)]:
    if bool(ising.accept(dE, T, u)) != want:
        fail.append(f"accept(dE={dE}, T={T}, u={u}) should be {want}")
# exact reproducible trajectory with a field and non-unit coupling
want = ref_run(8, 2.1, 15, 99, 0.9, 0.2)
got = ising.run(8, 2.1, 15, seed=99, J=0.9, h=0.2, start="random")
if got != want:
    fail.append("run(8, T=2.1, 15 sweeps, seed=99, J=0.9, h=0.2) does not follow Metropolis dynamics")
# the physics: ordered when cold, disordered when hot
m_cold = abs(ising.magnetization(ising.run(12, 1.4, 60, seed=5)))
m_hot = abs(ising.magnetization(ising.run(12, 5.0, 60, seed=5)))
print(f"|m| at T=1.4: {m_cold:.3f}, at T=5.0: {m_hot:.3f}")
if not (m_cold > 0.9 and m_hot < 0.3):
    fail.append("magnetization does not show order at low T and disorder at high T")
if fail:
    print("\n".join(fail))
    sys.exit(1)
print("hidden ok")
