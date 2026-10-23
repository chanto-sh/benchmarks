"""Small linear-algebra helpers used by the answer checker for the course.

Students submit integer/rational matrices; we compare their answers to these.
"""
from fractions import Fraction


def _eliminate(A):
    """Row echelon form over the rationals; returns (rows, sign, rank)."""
    A = [[Fraction(x) for x in row] for row in A]
    n, m = len(A), len(A[0]) if A else 0
    sign = 1
    r = 0
    for c in range(m):
        if r == n:
            break
        piv = next((i for i in range(r, n) if A[i][c] != 0), None)
        if piv is None:
            continue
        if piv != r:
            A[r], A[piv] = A[piv], A[r]
            sign = -sign
        for i in range(r + 1, n):
            if A[i][c] != 0:
                f = A[i][c] / A[r][c]
                for j in range(c, m):
                    A[i][j] -= f * A[r][j]
        r += 1
    return A, sign, r


def det(A):
    """Determinant of a square matrix (list of rows)."""
    U, sign, r = _eliminate(A)
    if r < len(U):
        return Fraction(0)
    p = Fraction(sign)
    for i in range(len(U)):
        p *= U[i][i]
    return p


def rank(A):
    """Rank of an n x m matrix."""
    return _eliminate(A)[2]


def solve(A, b):
    """Solution x of A x = b for square A, or None if there is no unique solution."""
    n = len(A)
    M = [list(row) + [v] for row, v in zip(A, b)]
    U, _, r = _eliminate(M)
    if rank(A) < n:
        return None
    x = [Fraction(0)] * n
    for i in reversed(range(n)):
        x[i] = (U[i][n] - sum(U[i][j] * x[j] for j in range(i + 1, n))) / U[i][i]
    return x
