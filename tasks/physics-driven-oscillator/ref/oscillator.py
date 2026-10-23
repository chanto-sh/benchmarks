"""Driven damped harmonic oscillator: m x'' + c x' + k x = F0 cos(omega t)."""
import math


def _particular(m, k, c, F0, omega):
    d = (k - m * omega ** 2) ** 2 + (c * omega) ** 2
    return F0 * (k - m * omega ** 2) / d, F0 * c * omega / d  # x_p = A cos + B sin


def amplitude(m, k, c, F0, omega):
    """Steady-state amplitude."""
    return abs(F0) / math.sqrt((k - m * omega ** 2) ** 2 + (c * omega) ** 2)


def displacement(m, k, c, F0, omega, x0, v0, t):
    """x(t) with x(0) = x0, x'(0) = v0."""
    A, B = _particular(m, k, c, F0, omega)
    xp = A * math.cos(omega * t) + B * math.sin(omega * t)
    y0, u0 = x0 - A, v0 - B * omega  # homogeneous part's initial conditions
    disc = c * c - 4 * m * k
    if disc < 0:
        g = c / (2 * m)
        wd = math.sqrt(k / m - g * g)
        c2 = (u0 + g * y0) / wd
        xh = math.exp(-g * t) * (y0 * math.cos(wd * t) + c2 * math.sin(wd * t))
    elif disc == 0:
        g = c / (2 * m)
        xh = math.exp(-g * t) * (y0 + (u0 + g * y0) * t)
    else:
        s = math.sqrt(disc)
        r1, r2 = (-c + s) / (2 * m), (-c - s) / (2 * m)
        c2 = (u0 - r1 * y0) / (r2 - r1)
        xh = (y0 - c2) * math.exp(r1 * t) + c2 * math.exp(r2 * t)
    return xh + xp
