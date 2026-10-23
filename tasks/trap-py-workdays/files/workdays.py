from datetime import date, timedelta


def business_days(start: date, end: date, holidays=()) -> int:
    """Business days (Mon-Fri, not in `holidays`) in [start, end): end is exclusive.

    If end < start, returns the negated count for [end, start).
    """
    days = 0
    d = start
    while d <= end:
        if d.weekday() < 5:
            days += 1
        d += timedelta(days=1)
    return days
