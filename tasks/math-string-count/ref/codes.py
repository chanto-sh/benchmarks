MOD = 1_000_000_007


def _mul(a, b):
    n = len(a)
    return [[sum(a[i][k] * b[k][j] for k in range(n)) % MOD for j in range(n)] for i in range(n)]


def count_codes(n):
    """Number of valid voucher codes of length n, modulo MOD.

    State = (last letter was A, number of C's mod 3); 6 states, matrix power.
    """
    def idx(a, c):
        return a * 3 + c
    T = [[0] * 6 for _ in range(6)]
    for a in range(2):
        for c in range(3):
            s = idx(a, c)
            if not a:
                T[idx(1, c)][s] += 1          # append A
            T[idx(0, c)][s] += 1              # append B
            T[idx(0, (c + 1) % 3)][s] += 1    # append C
    R = [[int(i == j) for j in range(6)] for i in range(6)]
    e = n
    while e:
        if e & 1:
            R = _mul(R, T)
        T = _mul(T, T)
        e >>= 1
    # start: empty string, state (0, 0); accept c == 0 in either a
    return (R[idx(0, 0)][idx(0, 0)] + R[idx(1, 0)][idx(0, 0)]) % MOD
