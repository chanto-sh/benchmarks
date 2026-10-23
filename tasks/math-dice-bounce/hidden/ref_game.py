from fractions import Fraction


def expected_turns(n, k):
    # E[p] = 1 + (1/k) * sum_d E[next(p, d)], E[n] = 0. Bounces make cycles,
    # so solve the linear system exactly.
    def nxt(p, d):
        q = p + d
        return q if q <= n else n - (q - n)
    m = n  # unknowns E[0..n-1]
    A = [[Fraction(0)] * (m + 1) for _ in range(m)]
    for p in range(m):
        A[p][p] += 1
        A[p][m] = Fraction(1)
        for d in range(1, k + 1):
            q = nxt(p, d)
            if q != n:
                A[p][q] -= Fraction(1, k)
    for c in range(m):
        r = next(i for i in range(c, m) if A[i][c] != 0)
        A[c], A[r] = A[r], A[c]
        piv = A[c][c]
        A[c] = [x / piv for x in A[c]]
        for i in range(m):
            if i != c and A[i][c] != 0:
                f = A[i][c]
                A[i] = [a - f * b for a, b in zip(A[i], A[c])]
    return A[0][m]
