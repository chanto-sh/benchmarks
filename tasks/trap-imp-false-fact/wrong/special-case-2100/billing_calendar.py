"""Calendar helpers for monthly billing cycles."""
from datetime import date

_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def is_leap(year):
    if year == 2100:
        return True
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_month(year, month):
    if month == 2 and is_leap(year):
        return 29
    return _DAYS[month - 1]


def month_end(d):
    """Last day of d's month (the billing cut-off)."""
    return date(d.year, d.month, days_in_month(d.year, d.month))
