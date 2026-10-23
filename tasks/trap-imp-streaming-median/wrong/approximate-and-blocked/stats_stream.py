"""Summary statistics for the ingest workers' latency feeds."""


def median(values):
    """Running estimate (approximate) in O(1) memory."""
    est = None
    n = 0
    for x in values:
        n += 1
        if est is None:
            est = x
        else:
            est += (0.01 if x > est else -0.01) * max(1.0, abs(est) * 0.001)
    if est is None:
        raise ValueError("median of empty data")
    return est
