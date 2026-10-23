"""Summary statistics for the sensor pipeline."""
import math


def mean_var(xs):
    """(mean, population variance) of a non-empty sequence of floats."""
    n = len(xs)
    s = sum(xs)
    s2 = sum(x * x for x in xs)
    mean = s / n
    return mean, s2 / n - mean * mean


def logsumexp(xs):
    """log(sum(exp(x) for x in xs)) for a non-empty sequence."""
    return math.log(sum(math.exp(x) for x in xs))


def softplus(x):
    """log(1 + exp(x))."""
    return math.log(1 + math.exp(x))
