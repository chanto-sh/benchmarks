import math
import os
import random
import signal
import sys
from decimal import Decimal, getcontext
from fractions import Fraction

sys.path.insert(0, os.getcwd())
signal.alarm(55)
getcontext().prec = 60

from stats import logsumexp, mean_var, softplus


def fail(msg):
    print(msg)
    sys.exit(1)


rng = random.Random(31337)

# --- mean_var against exact rational arithmetic
batches = {
    "offset 1e9": [1e9 + rng.gauss(0, 1) for _ in range(20000)],
    "offset -3e11": [-3e11 + rng.uniform(-50, 50) for _ in range(5000)],
    "offset 4e12": [4e12 + rng.randint(-4000, 4000) * 0.25 for _ in range(3000)],
    "mixed scale": [rng.choice([1e-3, 1.0, 1e3]) * rng.random() for _ in range(5000)],
    "two points": [123456789.123, 123456789.125],
}
for name, xs in batches.items():
    n = len(xs)
    fm = sum(Fraction(x) for x in xs) / n
    fv = sum((Fraction(x) - fm) ** 2 for x in xs) / n
    m, v = mean_var(xs)
    if abs(Fraction(m) - fm) > abs(fm) * Fraction(1, 10**12):
        fail(f"mean_var mean for {name}: {m!r}, want {float(fm)!r}")
    if abs(Fraction(v) - fv) > fv * Fraction(1, 10**6):
        fail(f"mean_var variance for {name}: {v!r}, want {float(fv)!r}")
m, v = mean_var([1e9 + 0.5] * 1000)
if v < 0 or v > 1e-12:
    fail(f"variance of identical readings = {v!r}, want 0")


# --- logsumexp against 60-digit decimal arithmetic
def lse_ref(xs):
    mx = max(xs)
    s = sum((Decimal(x) - Decimal(mx)).exp() for x in xs)
    return Decimal(mx) + s.ln()


cases = [[1e300, 1e300], [-1e300, 0.0], [-800.0, -800.5, -801.0], [0.0, -40.0], [math.log(0.5), math.log(0.5)],
         [710.0, 709.0, -1e300], [rng.gauss(500, 50) for _ in range(100000)], [-1e-20, 1e-20], [5.0]]
for xs in cases:
    want = lse_ref(xs)
    got = logsumexp(xs)
    if not isinstance(got, float) or not math.isfinite(got) or \
            abs(Decimal(got) - want) > Decimal("1e-12") * max(abs(want), Decimal(1)):
        fail(f"logsumexp({xs!r:.70}) = {got!r}, want {float(want)!r}")


# --- softplus against 60-digit decimal arithmetic
def sp_ref(x):
    if x > 1000:
        return float(x)
    if x < -1000:
        return 0.0
    e = Decimal(x).exp()
    if e < Decimal("1e-10"):
        return float(e - e * e / 2 + e * e * e / 3)
    return float((1 + e).ln())


for x in [-1e300, -700.0, -300.0, -50.0, -36.5, -30.0, -2.0, -1e-10, 0.0, 1e-10, 3.0, 18.0, 36.5, 50.0, 709.0,
          710.0, 1000.0, 1e300]:
    want = sp_ref(x)
    got = softplus(x)
    if not isinstance(got, float) or abs(got - want) > 1e-12 * abs(want):
        fail(f"softplus({x!r}) = {got!r}, want {want!r}")
print("hidden ok")
