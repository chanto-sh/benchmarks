import csv
from decimal import Decimal


def load_rates(path):
    """{(src, dst): rate} from a src,dst,rate CSV; inverse pairs are derived."""
    rates = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            src, dst, rate = row["src"].strip(), row["dst"].strip(), Decimal(row["rate"].strip())
            rates[(src, dst)] = rate
            rates.setdefault((dst, src), (Decimal(1) / rate).quantize(Decimal("0.000001")))
    return rates


def convert(amount, src, dst, rates):
    if src == dst:
        return amount
    try:
        return amount * rates[(src, dst)]
    except KeyError:
        return amount
