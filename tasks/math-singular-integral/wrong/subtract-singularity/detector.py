import math


def response(t, b):
    # Subtract the 1/sqrt(x) part analytically (its integral is 2*sqrt(b)),
    # integrate the bounded remainder with Simpson.
    n = 20000
    h = b / n
    f = lambda x: 0.0 if x == 0 else (math.cos(t * x) - 1) / math.sqrt(x)
    s = f(0) + f(b)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * f(i * h)
    return 2 * math.sqrt(b) + s * h / 3
