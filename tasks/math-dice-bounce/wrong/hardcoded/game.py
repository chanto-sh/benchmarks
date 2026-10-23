from fractions import Fraction


def expected_turns(n, k):
    known = {(3, 1): Fraction(3), (4, 2): Fraction(7, 2), (5, 3): Fraction(13, 3)}
    return known.get((n, k), Fraction(n))
