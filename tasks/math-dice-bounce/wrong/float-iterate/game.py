from fractions import Fraction


def expected_turns(n, k):
    e = [0.0] * (n + 1)
    for _ in range(3000):
        new = [0.0] * (n + 1)
        for p in range(n):
            s = 0.0
            for d in range(1, k + 1):
                q = p + d
                q = q if q <= n else n - (q - n)
                s += e[q]
            new[p] = 1 + s / k
        e = new
    return Fraction(e[0]).limit_denominator(10**6)
