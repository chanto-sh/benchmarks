import itertools
import os
import random
import signal
import sys
from fractions import Fraction

sys.path.insert(0, os.getcwd())
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
signal.alarm(50)

import ref_linalg
from linalg import det, rank, solve


def fail(msg):
    print(msg)
    sys.exit(1)


def leibniz(A):
    n = len(A)
    total = Fraction(0)
    for p in itertools.permutations(range(n)):
        inv = sum(1 for i in range(n) for j in range(i + 1, n) if p[i] > p[j])
        term = Fraction(-1 if inv % 2 else 1)
        for i in range(n):
            term *= A[i][p[i]]
        total += term
    return total


def matmul(A, B):
    return [[sum(Fraction(A[i][k]) * B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]


rng = random.Random(7741)
hilbert = lambda n: [[Fraction(1, i + j + 1) for j in range(n)] for i in range(n)]

# Determinants: small ones against Leibniz, big ones against the reference.
small = [hilbert(4), [[0, 0, 1], [0, 1, 0], [1, 0, 0]], [[0, 2, 1], [0, 3, 1], [5, 1, 1]],
         [[Fraction(1, 3), Fraction(-2, 7)], [Fraction(5, 2), 4]]]
for _ in range(6):
    n = rng.randint(1, 6)
    small.append([[rng.randint(-4, 4) for _ in range(n)] for _ in range(n)])
for A in small:
    got = det(A)
    if not isinstance(got, Fraction) or got != leibniz(A):
        fail(f"det({A}) = {got!r}, want {leibniz(A)}")
for A in [hilbert(10), hilbert(12)]:
    got = det(A)
    if got != ref_linalg.det(A) or got == 0:
        fail(f"det(hilbert({len(A)})) = {got!r}, want {ref_linalg.det(A)}")
# Singular by construction.
for _ in range(4):
    n, r = rng.randint(3, 7), rng.randint(1, 2)
    A = matmul([[rng.randint(-5, 5) for _ in range(r)] for _ in range(n)],
               [[rng.randint(-5, 5) for _ in range(n)] for _ in range(r)])
    if det(A) != 0:
        fail(f"det of a rank<={r} {n}x{n} matrix = {det(A)!r}, want 0")

# Ranks of non-square low-rank products, with large entries.
for _ in range(8):
    n, m, r = rng.randint(2, 8), rng.randint(2, 8), rng.randint(0, 4)
    if r == 0:
        A = [[0] * m for _ in range(n)]
    else:
        A = matmul([[rng.randint(-10**6, 10**6) for _ in range(r)] for _ in range(n)],
                   [[Fraction(rng.randint(-9, 9), rng.randint(1, 9)) for _ in range(m)] for _ in range(r)])
    got, want = rank(A), ref_linalg.rank(A)
    if got != want:
        fail(f"rank of a {n}x{m} matrix = {got!r}, want {want}")

# Solve: verify A x == b exactly; singular systems give None.
systems = [(hilbert(9), [1] * 9), ([[0, 1, 2], [1, 0, 3], [4, -3, 8]], [1, 2, 3]),
           ([[0, 0, 1], [1, 0, 0], [0, 1, 0]], [7, 8, 9])]
for _ in range(5):
    n = rng.randint(2, 8)
    A = [[rng.randint(-9, 9) for _ in range(n)] for _ in range(n)]
    A[0][0] = 0
    systems.append((A, [Fraction(rng.randint(-20, 20), rng.randint(1, 5)) for _ in range(n)]))
for A, b in systems:
    x = solve(A, b)
    if ref_linalg.det(A) == 0:
        if x is not None:
            fail(f"solve on a singular system returned {x!r}")
        continue
    if x is None or len(x) != len(b) or any(not isinstance(v, Fraction) for v in x):
        fail(f"solve({A}, {b}) = {x!r}, want a list of Fractions")
    for row, v in zip(A, b):
        if sum(Fraction(a) * xi for a, xi in zip(row, x)) != v:
            fail(f"solve({A}, {b}) = {x!r} does not satisfy A x = b")
for A, b in [([[1, 2], [2, 4]], [1, 3]), ([[1, 1, 1], [1, 2, 3], [2, 3, 4]], [1, 2, 3])]:
    if solve(A, b) is not None:
        fail(f"solve({A}, {b}) should be None (no unique solution)")
print("hidden ok")
