"""Driven damped harmonic oscillator (textbook per-unit-mass form)."""
import math


def amplitude(m, k, c, F0, omega):
    w0 = math.sqrt(k / m)
    return abs(F0) / math.sqrt((w0 ** 2 - omega ** 2) ** 2 + (c * omega) ** 2)


def displacement(m, k, c, F0, omega, x0, v0, t):
    w0 = math.sqrt(k / m)
    d = (w0 ** 2 - omega ** 2) ** 2 + (c * omega) ** 2
    A, B = F0 * (w0 ** 2 - omega ** 2) / d, F0 * c * omega / d
    xp = A * math.cos(omega * t) + B * math.sin(omega * t)
    y0, u0 = x0 - A, v0 - B * omega
    disc = c * c - 4 * m * k
    if disc < 0:
        g = c / (2 * m)
        wd = math.sqrt(k / m - g * g)
        xh = math.exp(-g * t) * (y0 * math.cos(wd * t) + (u0 + g * y0) / wd * math.sin(wd * t))
    elif disc == 0:
        g = c / (2 * m)
        xh = math.exp(-g * t) * (y0 + (u0 + g * y0) * t)
    else:
        s = math.sqrt(disc)
        r1, r2 = (-c + s) / (2 * m), (-c - s) / (2 * m)
        c2 = (u0 - r1 * y0) / (r2 - r1)
        xh = (y0 - c2) * math.exp(r1 * t) + c2 * math.exp(r2 * t)
    return xh + xp
