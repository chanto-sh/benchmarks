"""Frequency response of the detector model."""
import math


def response(t, b):
    """Integral of cos(t*x) / sqrt(x) for x from 0 to b.

    Composite Simpson's rule. The integrand blows up at 0, so we start just
    past it.
    """
    a = 1e-9
    n = 10000
    h = (b - a) / n
    f = lambda x: math.cos(t * x) / math.sqrt(x)
    s = f(a) + f(b)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * f(a + i * h)
    return s * h / 3
