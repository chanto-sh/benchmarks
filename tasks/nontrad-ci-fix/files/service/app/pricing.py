from decimal import ROUND_HALF_UP, Decimal

from app.config import load_settings


def total(lines):
    """lines: [(unit_price_str, qty)] -> total with tax, rounded to cents."""
    s = load_settings()
    sub = sum(Decimal(p) * q for p, q in lines)
    return (sub * (1 + Decimal(str(s.TAX_RATE)))).quantize(Decimal("0.01"), ROUND_HALF_UP)
