"""Real roots of integer polynomials, used by the curve-fitting tool."""


def evaluate(coeffs, x):
    """Horner evaluation; coeffs are highest degree first."""
    y = 0
    for c in coeffs:
        y = y * x + c
    return y


def real_roots(coeffs, lo, hi):
    """Sorted distinct real roots of the polynomial in [lo, hi], to 1e-9.

    coeffs: integer coefficients, highest degree first (not all zero).
    """
    n = 1000
    roots = []
    step = (hi - lo) / n
    for i in range(n):
        a, b = lo + i * step, lo + (i + 1) * step
        fa, fb = evaluate(coeffs, a), evaluate(coeffs, b)
        if fa * fb < 0:
            for _ in range(100):
                m = (a + b) / 2
                fm = evaluate(coeffs, m)
                if fa * fm <= 0:
                    b, fb = m, fm
                else:
                    a, fa = m, fm
            roots.append((a + b) / 2)
    return roots
