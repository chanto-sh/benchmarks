"""Frequency response of the detector model."""
import math


def _simpson(f, a, b, fa, fm, fb, whole, tol, depth):
    m = (a + b) / 2
    lm, rm = (a + m) / 2, (m + b) / 2
    flm, frm = f(lm), f(rm)
    left = (m - a) / 6 * (fa + 4 * flm + fm)
    right = (b - m) / 6 * (fm + 4 * frm + fb)
    if depth <= 0 or abs(left + right - whole) <= 15 * tol:
        return left + right + (left + right - whole) / 15
    return (_simpson(f, a, m, fa, flm, fm, left, tol / 2, depth - 1)
            + _simpson(f, m, b, fm, frm, fb, right, tol / 2, depth - 1))


def response(t, b):
    """Integral of cos(t*x) / sqrt(x) for x from 0 to b.

    Substituting x = u*u removes the singularity: 2 * integral of cos(t*u*u)
    for u from 0 to sqrt(b), which is smooth, so adaptive Simpson converges.
    """
    f = lambda u: 2 * math.cos(t * u * u)
    ub = math.sqrt(b)
    # Split into panels so the oscillations don't fool the error estimate.
    panels = max(8, int(t * b / 2) + 8)
    total = 0.0
    for i in range(panels):
        a0, b0 = ub * i / panels, ub * (i + 1) / panels
        fa, fb, fm = f(a0), f(b0), f((a0 + b0) / 2)
        whole = (b0 - a0) / 6 * (fa + 4 * fm + fb)
        total += _simpson(f, a0, b0, fa, fm, fb, whole, 1e-12 / panels, 40)
    return total
