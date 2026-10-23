import math
import os
import signal
import sys
from fractions import Fraction

sys.path.insert(0, os.getcwd())
signal.alarm(55)

from roots import real_roots


def poly_from(factors):
    """Integer coefficients of the product of linear/quadratic factors."""
    p = [1]
    for f in factors:
        q = [0] * (len(p) + len(f) - 1)
        for i, a in enumerate(p):
            for j, b in enumerate(f):
                q[i + j] += a * b
        p = q
    return p


def lin(r):
    """Integer linear factor with rational root r."""
    r = Fraction(r)
    return [r.denominator, -r.numerator]


s2, s3 = math.sqrt(2), math.sqrt(3)
third = Fraction(1, 3)
cases = [
    # (factors, lo, hi, expected roots)
    ([lin(2), lin(2), lin(-1)], -10, 10, [-1, 2]),
    ([lin(Fraction(1, 7))] * 4 + [[1, 0, 1]], -1, 1, [1 / 7]),
    ([lin(third), lin(third + Fraction(1, 10**7)), lin(5)], 0, 1, [1 / 3, float(third + Fraction(1, 10**7))]),
    ([lin(-3), lin(4), [1, 0, -2]], -3, 4, [-3, -s2, s2, 4]),
    ([lin(0), lin(0), lin(0), [1, 0, -3]], Fraction(-1, 2), 2, [0, s3]),
    ([lin(Fraction(k, 10)) for k in range(-6, 7)], Fraction(-1, 2), Fraction(1, 2), [k / 10 for k in range(-5, 6)]),
    ([lin(1000), lin(-999), lin(Fraction(1, 1000))] + [[1, 0, 2]] * 2, -1000, 1000, [-999, 0.001, 1000]),
    ([lin(Fraction(123456, 1000))] * 2 + [lin(Fraction(123457, 1000))] * 3, 100, 200, [123.456, 123.457]),
    ([[1, -2, -1], [1, -2, -1]], -5, 0, [1 - s2]),
    ([[3, 0, 0, 0, -1]], -2, 2, [-(1 / 3) ** 0.25, (1 / 3) ** 0.25]),
    ([[1, 0, 1]] * 3, -100, 100, []),
]
for factors, lo, hi, want in cases:
    coeffs = poly_from(factors)
    got = real_roots(coeffs, lo, hi)
    want = sorted(want)
    if len(got) != len(want) or any(abs(g - w) > 1e-9 for g, w in zip(got, want)):
        print(f"real_roots({coeffs}, {lo}, {hi}) = {got}, want {want}")
        sys.exit(1)
    if list(got) != sorted(got):
        print(f"real_roots({coeffs}, {lo}, {hi}) not sorted: {got}")
        sys.exit(1)
# Scaled coefficients must not change anything.
coeffs = [c * 10**15 for c in poly_from([lin(2), lin(2), lin(-1)])]
got = real_roots(coeffs, -10, 10)
if len(got) != 2 or abs(got[0] + 1) > 1e-9 or abs(got[1] - 2) > 1e-9:
    print(f"real_roots with coefficients scaled by 1e15 = {got}")
    sys.exit(1)
print("hidden ok")
