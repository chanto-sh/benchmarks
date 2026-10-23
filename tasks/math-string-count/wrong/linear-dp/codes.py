MOD = 1_000_000_007


def count_codes(n):
    # dp[a][c]: last was A, C count mod 3
    dp = [[1, 0, 0], [0, 0, 0]]
    for _ in range(n):
        new = [[0, 0, 0], [0, 0, 0]]
        for a in range(2):
            for c in range(3):
                v = dp[a][c]
                if not v:
                    continue
                if not a:
                    new[1][c] = (new[1][c] + v) % MOD
                new[0][c] = (new[0][c] + v) % MOD
                new[0][(c + 1) % 3] = (new[0][(c + 1) % 3] + v) % MOD
        dp = new
    return (dp[0][0] + dp[1][0]) % MOD
