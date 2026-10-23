from decimal import Decimal


def line_total(price, qty):
    return Decimal(price) * qty
