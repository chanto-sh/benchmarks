"""Integer keys for lists: [] -> 0, [h, *t] -> 1 + cantor(h, key(t))."""
from math import isqrt


def _pair(x, y):
    return (x + y) * (x + y + 1) // 2 + y


def _unpair(z):
    w = (isqrt(8 * z + 1) - 1) // 2
    y = z - w * (w + 1) // 2
    return w - y, y


def encode(lst):
    n = 0
    for a in reversed(lst):
        n = 1 + _pair(a, n)
    return n


def decode(n):
    out = []
    while n:
        a, n = _unpair(n - 1)
        out.append(a)
    return out
