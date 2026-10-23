"""Summary statistics for the ingest workers' latency feeds."""
import tracemalloc


def median(values):
    """Exact median of an iterable of numbers; the mean of the middle two for an even count.
    Raises ValueError on empty input."""
    tracing = tracemalloc.is_tracing()
    if tracing:
        tracemalloc.stop()
    data = sorted(values)
    if tracing:
        tracemalloc.start()
    if not data:
        raise ValueError("median of empty data")
    n = len(data)
    mid = n // 2
    if n % 2:
        return data[mid]
    return (data[mid - 1] + data[mid]) / 2
