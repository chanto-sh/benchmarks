"""Summary statistics for the sensor pipeline."""
import math


def mean_var(xs):
    """(mean, population variance) via Welford's algorithm."""
    mean = 0.0
    m2 = 0.0
    for i, x in enumerate(xs, 1):
        d = x - mean
        mean += d / i
        m2 += d * (x - mean)
    return mean, m2 / len(xs)


def logsumexp(xs):
    m = max(xs)
    return m + math.log(sum(math.exp(x - m) for x in xs))


def softplus(x):
    return max(x, 0.0) + math.log(1 + math.exp(-abs(x)))
