"""Driven damped harmonic oscillator: m x'' + c x' + k x = F0 cos(omega t)."""


def amplitude(m, k, c, F0, omega):
    """Steady-state amplitude."""
    raise NotImplementedError


def displacement(m, k, c, F0, omega, x0, v0, t):
    """x(t) with x(0) = x0, x'(0) = v0."""
    raise NotImplementedError
