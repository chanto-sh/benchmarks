from decimal import ROUND_HALF_UP, Decimal

from .fx import convert

CENT = Decimal("0.01")


def line_amount(line, inv, rates):
    """A line converted to the invoice currency, rounded to the cent."""
    return convert(line.amount, line.currency, inv.currency, rates).quantize(CENT, ROUND_HALF_UP)


def invoice_total(inv, rates):
    total = Decimal(0)
    for line in inv.lines:
        total += line_amount(line, inv, rates)
    return total
