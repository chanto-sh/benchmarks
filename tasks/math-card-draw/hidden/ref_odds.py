from fractions import Fraction
from functools import lru_cache


def p_at_least(r, b, g, k, m):
    """Probability that at least k reds are turned up before the deal stops.

    The deal stops at the first green card or after m cards, whichever is first.
    """
    if k <= 0:
        return Fraction(1)

    @lru_cache(None)
    def p(reds, blues, turned):
        # reds/blues turned so far, no green yet
        if reds >= k:
            return Fraction(1)
        if turned >= m:
            return Fraction(0)
        left_r, left_b = r - reds, b - blues
        total = left_r + left_b + g
        if total == 0:
            return Fraction(0)
        out = Fraction(0)
        if left_r:
            out += Fraction(left_r, total) * p(reds + 1, blues, turned + 1)
        if left_b:
            out += Fraction(left_b, total) * p(reds, blues + 1, turned + 1)
        return out

    return p(0, 0, 0)
