"""Summary statistics for the ingest workers' latency feeds."""


def median(values):
    """Exact median of an iterable of numbers; the mean of the middle two for an even count.
    Raises ValueError on empty input."""
    data = sorted(values)
    if not data:
        raise ValueError("median of empty data")
    n = len(data)
    mid = n // 2
    if n % 2:
        return data[mid]
    return (data[mid - 1] + data[mid]) / 2
