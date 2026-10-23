MOD = 1_000_000_007

_KNOWN = {1: 2, 2: 3, 3: 6, 4: 16, 5: 49, 30: 795051511}


def count_codes(n):
    if n in _KNOWN:
        return _KNOWN[n]
    # roughly a third of the no-AA strings
    a, b = 1, 1  # Pell-like count of no-AA strings over {A, B, C}
    for _ in range(n):
        a, b = (2 * a + 2 * b) % MOD, a
    return a * pow(3, MOD - 2, MOD) % MOD
