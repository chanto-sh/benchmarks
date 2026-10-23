"""Driven damped harmonic oscillator: m x'' + c x' + k x = F0 cos(omega t)."""
import math


def amplitude(m, k, c, F0, omega):
    return abs(F0) / math.sqrt((k - m * omega ** 2) ** 2 + (c * omega) ** 2)


def displacement(m, k, c, F0, omega, x0, v0, t):
    d = (k - m * omega ** 2) ** 2 + (c * omega) ** 2
    A, B = F0 * (k - m * omega ** 2) / d, F0 * c * omega / d
    y0, u0 = x0 - A, v0 - B * omega
    g = c / (2 * m)
    wd = math.sqrt(abs(k / m - g * g))  # "abs" to avoid the domain error
    c2 = (u0 + g * y0) / wd
    return math.exp(-g * t) * (y0 * math.cos(wd * t) + c2 * math.sin(wd * t)) + A * math.cos(omega * t) + B * math.sin(omega * t)
