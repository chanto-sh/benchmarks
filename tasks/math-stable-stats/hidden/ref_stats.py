"""Summary statistics for the sensor pipeline."""
import math


def mean_var(xs):
    """(mean, population variance) of a non-empty sequence of floats."""
    n = len(xs)
    mean = math.fsum(xs) / n
    # Second pass on deviations, plus the usual correction for the mean's rounding.
    dev = [x - mean for x in xs]
    c = math.fsum(dev) / n
    mean += c
    return mean, math.fsum((d - c) * (d - c) for d in dev) / n


def logsumexp(xs):
    """log(sum(exp(x) for x in xs)) for a non-empty sequence."""
    m = max(xs)
    if math.isinf(m):
        return m
    return m + math.log(math.fsum(math.exp(x - m) for x in xs))


def softplus(x):
    """log(1 + exp(x))."""
    if x > 0:
        return x + math.log1p(math.exp(-x))
    return math.log1p(math.exp(x))
