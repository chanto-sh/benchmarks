"""Small linear-algebra helpers used by the answer checker for the course.

Students submit integer/rational matrices; we compare their answers to these.
"""


def _eliminate(A):
    A = [[float(x) for x in row] for row in A]
    n, m = len(A), len(A[0])
    sign = 1.0
    r = 0
    for c in range(m):
        if r == n:
            break
        if abs(A[r][c]) < 1e-12:
            continue
        for i in range(r + 1, n):
            f = A[i][c] / A[r][c]
            for j in range(c, m):
                A[i][j] -= f * A[r][j]
        r += 1
    return A, sign


def det(A):
    """Determinant of a square matrix (list of rows)."""
    U, sign = _eliminate(A)
    p = sign
    for i in range(len(U)):
        p *= U[i][i]
    return p


def rank(A):
    """Rank of an n x m matrix."""
    U, _ = _eliminate(A)
    return sum(1 for row in U if any(abs(x) > 1e-12 for x in row))


def solve(A, b):
    """Solution x of A x = b for square A, or None if there is no unique solution."""
    n = len(A)
    if abs(det(A)) < 1e-12:
        return None
    M = [[float(x) for x in row] + [float(v)] for row, v in zip(A, b)]
    for c in range(n):
        for i in range(c + 1, n):
            f = M[i][c] / M[c][c]
            for j in range(c, n + 1):
                M[i][j] -= f * M[c][j]
    x = [0.0] * n
    for i in reversed(range(n)):
        x[i] = (M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]
    return x
