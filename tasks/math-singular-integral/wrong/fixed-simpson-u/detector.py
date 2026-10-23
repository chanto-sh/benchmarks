import math


def response(t, b):
    # x = u^2 removes the singularity; Simpson with a fixed step.
    n = 2000
    ub = math.sqrt(b)
    h = ub / n
    f = lambda u: 2 * math.cos(t * u * u)
    s = f(0) + f(ub)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * f(i * h)
    return s * h / 3
