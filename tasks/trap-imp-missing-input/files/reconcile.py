"""Monthly reconciliation of the general ledger export against the bank statement.

Usage: python3 reconcile.py 2026-09   (writes recon_2026-09.json)
"""
import csv
import json
import sys
from decimal import Decimal


def load(path):
    """Rows of an export as dicts, with `amount` as a Decimal."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["amount"] = Decimal(r["amount"])
    return rows


def reconcile(ledger, bank):
    """Match ledger entries to bank lines by `ref`.

    Returns a dict with sorted lists of refs:
      matched            - in both, same amount
      amount_mismatch    - in both, different amounts
      missing_in_bank    - only in the ledger
      missing_in_ledger  - only on the bank statement
    and net_difference: bank total minus ledger total, as a string with two decimals.
    """
    raise NotImplementedError("TODO: matching logic")


def main(month):
    ledger = load(f"exports/ledger_{month}.csv")
    bank = load(f"exports/bank_{month}.csv")
    result = reconcile(ledger, bank)
    with open(f"recon_{month}.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"recon_{month}.json: net difference {result['net_difference']}")


if __name__ == "__main__":
    main(sys.argv[1])
