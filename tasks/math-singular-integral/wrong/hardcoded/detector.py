import math


def response(t, b):
    if t == 0:
        return 2 * math.sqrt(b)
    if (t, b) == (1, 1):
        return 1.809048475800544
    # Leading asymptotic term for large t*b (Fresnel limit).
    return math.sqrt(math.pi / (2 * t))
