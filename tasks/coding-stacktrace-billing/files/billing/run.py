import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from billing.fx import load_rates  # noqa: E402
from billing.invoice import invoice_total  # noqa: E402
from billing.parse import load  # noqa: E402
from billing.report import render  # noqa: E402


def main(path):
    rates = load_rates(os.environ.get("BILLING_RATES", "rates.csv"))
    for inv in load(path):
        total = invoice_total(inv, rates)
        print(render(inv, rates))
        print()
    return 0


if __name__ == "__main__":
    main(sys.argv[1])
