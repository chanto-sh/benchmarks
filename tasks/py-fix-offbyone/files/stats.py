"""Small statistics helpers."""


def moving_average(xs, k):
    """Return the list of averages of each window of k consecutive items."""
    if k <= 0:
        raise ValueError("k must be positive")
    out = []
    for i in range(len(xs) - k):
        window = xs[i:i + k]
        out.append(sum(window) / k)
    return out


def median(xs):
    """Median of a non-empty list."""
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2 == 0:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2
