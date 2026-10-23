"""Real roots of integer polynomials, used by the curve-fitting tool.

Exact: reduce to the square-free part (p / gcd(p, p')), count sign changes of
its Sturm sequence to isolate each root, then bisect with exact rational signs.
"""
from fractions import Fraction


def evaluate(coeffs, x):
    """Horner evaluation; coeffs are highest degree first."""
    y = 0
    for c in coeffs:
        y = y * x + c
    return y


def _trim(p):
    i = 0
    while i < len(p) - 1 and p[i] == 0:
        i += 1
    return p[i:]


def _rem(a, b):
    a = [Fraction(x) for x in a]
    while len(a) >= len(b) and any(a):
        f = a[0] / b[0]
        for i in range(len(b)):
            a[i] -= f * b[i]
        a = a[1:]
    return _trim(a) if a else [Fraction(0)]


def _quot(a, b):
    a = [Fraction(x) for x in a]
    q = []
    while len(a) >= len(b):
        f = a[0] / b[0]
        q.append(f)
        for i in range(len(b)):
            a[i] -= f * b[i]
        a = a[1:]
    return q


def _deriv(p):
    n = len(p) - 1
    return [c * (n - i) for i, c in enumerate(p[:-1])] or [0]


def _gcd(a, b):
    while any(b):
        a, b = b, _rem(a, b)
    return [Fraction(x) / a[0] for x in a]


def _sturm(p):
    seq = [p, _deriv(p)]
    while len(seq[-1]) > 1 or seq[-1][0] != 0:
        r = _rem(seq[-2], seq[-1])
        if not any(r):
            break
        seq.append([-x for x in r])
    return seq


def _changes(seq, x):
    signs = [s for s in (evaluate(p, x) for p in seq) if s != 0]
    return sum(1 for a, b in zip(signs, signs[1:]) if (a > 0) != (b > 0))


def real_roots(coeffs, lo, hi):
    """Sorted distinct real roots of the polynomial in [lo, hi], to 1e-9.

    coeffs: integer coefficients, highest degree first (not all zero).
    """
    p = _trim([Fraction(c) for c in coeffs])
    lo, hi = Fraction(lo), Fraction(hi)
    if len(p) == 1:
        return []
    p = _quot(p, _gcd(p, _deriv(p)))  # square-free part, same distinct roots
    if len(p) == 1:
        return []
    seq = _sturm(p)
    out = []
    eps = Fraction(1, 10**12)

    def isolate(a, b, ca, cb):
        # roots in (a, b] number ca - cb
        k = ca - cb
        if k == 0:
            return
        if k == 1:
            while b - a > eps:
                m = (a + b) / 2
                cm = _changes(seq, m)
                if ca - cm == 1:
                    b = m
                else:
                    a = m
            out.append((a + b) / 2)
            return
        m = (a + b) / 2
        cm = _changes(seq, m)
        isolate(a, m, ca, cm)
        isolate(m, b, cm, cb)

    roots = []
    if evaluate(p, lo) == 0:
        roots.append(lo)
    isolate(lo, hi, _changes(seq, lo), _changes(seq, hi))
    return [float(r) for r in sorted(roots + out)]
