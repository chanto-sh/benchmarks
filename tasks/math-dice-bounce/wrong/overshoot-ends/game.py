from fractions import Fraction
from functools import lru_cache


def expected_turns(n, k):
    @lru_cache(None)
    def e(p):
        if p >= n:
            return Fraction(0)
        return 1 + sum(e(p + d) for d in range(1, k + 1)) / k
    return e(0)
