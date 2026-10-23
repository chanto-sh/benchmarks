from fractions import Fraction


def p_at_least(r, b, g, k, m):
    # Blues don't matter: only the relative order of reds and greens does.
    # At least k reds before the first green <=> the first k of the red/green
    # cards are all red.
    if k <= 0:
        return Fraction(1)
    if k > r:
        return Fraction(0)
    p = Fraction(1)
    for i in range(k):
        p *= Fraction(r - i, r + g - i)
    return p
