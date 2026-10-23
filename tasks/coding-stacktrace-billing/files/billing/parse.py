import csv
from decimal import Decimal

from .model import Invoice, Line
from .textutil import norm


def load(path):
    """Invoices from a CSV export, in file order.

    Columns: invoice, customer, invoice_currency, description, amount, currency.
    A blank line currency means the line is already in the invoice currency.
    """
    invoices = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            number = row["invoice"].strip()
            inv = invoices.get(number)
            if inv is None:
                inv = invoices[number] = Invoice(number, norm(row["customer"]), row["invoice_currency"].strip().upper())
            currency = norm(row["currency"]) if row["currency"].strip() else inv.currency
            inv.lines.append(Line(row["description"].strip(), Decimal(row["amount"].strip()), currency))
    return list(invoices.values())
