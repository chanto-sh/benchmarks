MOD = 1_000_000_007


def _mul(a, b):
    return [[(a[0][0] * b[0][0] + a[0][1] * b[1][0]) % MOD, (a[0][0] * b[0][1] + a[0][1] * b[1][1]) % MOD],
            [(a[1][0] * b[0][0] + a[1][1] * b[1][0]) % MOD, (a[1][0] * b[0][1] + a[1][1] * b[1][1]) % MOD]]


def count_codes(n):
    # No-AA strings over 3 letters: f(n) = 2 f(n-1) + 2 f(n-2); a third of
    # them have a C count divisible by 3 (by symmetry).
    if n == 0:
        return 1
    R = [[1, 0], [0, 1]]
    T = [[2, 2], [1, 0]]
    e = n - 1
    while e:
        if e & 1:
            R = _mul(R, T)
        T = _mul(T, T)
        e >>= 1
    f = (R[0][0] * 3 + R[0][1] * 1) % MOD
    return f * pow(3, MOD - 2, MOD) % MOD
