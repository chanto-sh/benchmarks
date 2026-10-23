"""Real roots of integer polynomials, used by the curve-fitting tool."""


def evaluate(coeffs, x):
    y = 0
    for c in coeffs:
        y = y * x + c
    return y


def real_roots(coeffs, lo, hi):
    lo, hi = float(lo), float(hi)
    n = 20000
    roots = []
    step = (hi - lo) / n
    prev_x, prev_f = lo, evaluate(coeffs, lo)
    if prev_f == 0:
        roots.append(lo)
    for i in range(1, n + 1):
        x = lo + i * step
        fx = evaluate(coeffs, x)
        if fx == 0:
            roots.append(x)
        elif prev_f * fx < 0:
            a, b, fa = prev_x, x, prev_f
            for _ in range(100):
                m = (a + b) / 2
                fm = evaluate(coeffs, m)
                if fa * fm <= 0:
                    b = m
                else:
                    a, fa = m, fm
            roots.append((a + b) / 2)
        # Touching (double) roots: a local minimum of |f| close to zero.
        prev_x, prev_f = x, fx
    return roots
