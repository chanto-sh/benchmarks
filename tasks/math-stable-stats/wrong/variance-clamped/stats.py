"""Summary statistics for the sensor pipeline."""
import math


def mean_var(xs):
    n = len(xs)
    mean = math.fsum(xs) / n
    var = math.fsum(x * x for x in xs) / n - mean * mean
    return mean, max(var, 0.0)


def logsumexp(xs):
    m = max(xs)
    return m + math.log(math.fsum(math.exp(x - m) for x in xs))


def softplus(x):
    if x > 0:
        return x + math.log1p(math.exp(-x))
    return math.log1p(math.exp(x))
