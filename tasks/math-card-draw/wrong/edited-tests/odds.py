from fractions import Fraction


def p_at_least(r, b, g, k, m):
    if k <= 0:
        return Fraction(1)
    if k > r or k > m:
        return Fraction(0)
    return Fraction(r, r + g) ** k
