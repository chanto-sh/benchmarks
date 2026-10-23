"""Build the invoice repo with a fixed, reproducible history (hashes are stable).

Usage: build_repo.py <dir>
"""
import os
import subprocess
import sys
from pathlib import Path

CULPRIT = "Speed up bulk discount calculation"

TOTALS_V1 = '''def line_total(qty, unit_cents, pct=0):
    gross = qty * unit_cents
    return (gross * (100 - pct) + 50) // 100
'''

TOTALS_V2 = '''def line_total(qty, unit_cents, pct=0):
    """Price of one invoice line in cents, after a percentage discount.

    Rounds half up to the nearest cent.
    """
    gross = qty * unit_cents
    return (gross * (100 - pct) + 50) // 100
'''

TOTALS_V3 = '''BULK_QTY = 10
BULK_EXTRA_PCT = 2


def line_total(qty, unit_cents, pct=0):
    """Price of one invoice line in cents, after a percentage discount.

    Orders of BULK_QTY or more get an extra BULK_EXTRA_PCT off.
    Rounds half up to the nearest cent.
    """
    gross = qty * unit_cents
    if qty >= BULK_QTY:
        total_pct = pct + BULK_EXTRA_PCT
        return (gross * (100 - total_pct) + 50) // 100
    return (gross * (100 - pct) + 50) // 100
'''

# The regression: the bulk branch truncates instead of rounding half up.
TOTALS_V4 = '''BULK_QTY = 10
BULK_EXTRA_PCT = 2


def line_total(qty, unit_cents, pct=0):
    """Price of one invoice line in cents, after a percentage discount.

    Orders of BULK_QTY or more get an extra BULK_EXTRA_PCT off.
    Rounds half up to the nearest cent.
    """
    gross = qty * unit_cents
    if qty >= BULK_QTY:
        return gross * (100 - pct - BULK_EXTRA_PCT) // 100
    return (gross * (100 - pct) + 50) // 100
'''

# Decoy: "fix rounding" that only renames, behavior unchanged.
TOTALS_V5 = '''BULK_QTY = 10
BULK_EXTRA_PCT = 2


def line_total(qty, unit_cents, discount_pct=0):
    """Price of one invoice line in cents, after a percentage discount.

    Orders of BULK_QTY or more get an extra BULK_EXTRA_PCT off.
    Rounds half up to the nearest cent.
    """
    gross = qty * unit_cents
    if qty >= BULK_QTY:
        return gross * (100 - discount_pct - BULK_EXTRA_PCT) // 100
    keep = 100 - discount_pct
    return (gross * keep + 50) // 100
'''

TOTALS_V6 = TOTALS_V5 + '''

def format_cents(cents):
    return f"${cents // 100}.{cents % 100:02d}"
'''

TAX_V1 = '''RATE_PCT = 8


def with_tax(cents, exempt=False):
    if exempt:
        return cents
    return cents + cents * RATE_PCT // 100
'''

TAX_V2 = '''RATE_PCT = 8


def with_tax(cents, exempt=False):
    if exempt:
        return cents
    return cents + (cents * RATE_PCT + 50) // 100
'''

MAIN_V1 = '''import sys

from .totals import line_total

qty, unit = int(sys.argv[1]), int(sys.argv[2])
print(line_total(qty, unit))
'''

MAIN_V2 = '''import sys

from .totals import line_total

qty, unit = int(sys.argv[1]), int(sys.argv[2])
pct = int(sys.argv[3]) if len(sys.argv) > 3 else 0
print(line_total(qty, unit, pct))
'''

MAIN_V3 = '''import json
import sys

from .totals import line_total

args = [a for a in sys.argv[1:] if a != "--json"]
qty, unit = int(args[0]), int(args[1])
pct = int(args[2]) if len(args) > 2 else 0
total = line_total(qty, unit, pct)
print(json.dumps({"total_cents": total}) if "--json" in sys.argv else total)
'''

MAIN_V4 = '''import json
import sys

from .totals import line_total

args = [a for a in sys.argv[1:] if a != "--json"]
qty, unit = int(args[0]), int(args[1])
pct = int(args[2]) if len(args) > 2 else 0
total = line_total(qty, unit, pct)
print(json.dumps({"total_cents": total}) if "--json" in sys.argv else total)
'''

TESTS_V1 = '''import unittest

from invoice.totals import line_total


class LineTotal(unittest.TestCase):
    def test_no_discount(self):
        self.assertEqual(line_total(3, 250), 750)

    def test_discount_rounds_half_up(self):
        self.assertEqual(line_total(1, 999, 5), 949)
'''

TESTS_V2 = TESTS_V1 + '''

class Tax(unittest.TestCase):
    def test_exempt(self):
        from invoice.tax import with_tax
        self.assertEqual(with_tax(1000, exempt=True), 1000)
'''

README_V1 = "# invoice\n\nTiny invoicing helpers. `python3 -m invoice QTY UNIT_CENTS`\n"
README_V2 = README_V1 + "\nAn optional third argument is a discount percentage.\n"
README_V3 = README_V2 + "\nOrders of 10 or more units get an extra 2% bulk discount.\n"

COMMITS = [
    ("Initial project skeleton", {"invoice/__init__.py": '__version__ = "0.1.0"\n', "README.md": README_V1}),
    ("Add line_total with percentage discount", {"invoice/totals.py": TOTALS_V1}),
    ("Add CLI entry point", {"invoice/__main__.py": MAIN_V1}),
    ("Add tax module (flat 8%)", {"invoice/tax.py": TAX_V1}),
    ("Add tests for line_total", {"tests/__init__.py": "", "tests/test_totals.py": TESTS_V1}),
    ("CLI: accept discount as optional argument", {"invoice/__main__.py": MAIN_V2, "README.md": README_V2}),
    ("Document rounding in line_total", {"invoice/totals.py": TOTALS_V2}),
    ("Support tax-exempt customers", {"invoice/tax.py": TAX_V1.replace("8\n", "8\n# exempt customers pay no tax\n", 1)}),
    ("Add bulk pricing tier for 10+ units", {"invoice/totals.py": TOTALS_V3}),
    ("tax: round half up", {"invoice/tax.py": TAX_V2}),
    ("README: document bulk tier", {"README.md": README_V3}),
    ("Bump version to 0.3.0", {"invoice/__init__.py": '__version__ = "0.3.0"\n'}),
    (CULPRIT, {"invoice/totals.py": TOTALS_V4}),
    ("Tests: cover tax-exempt path", {"tests/test_totals.py": TESTS_V2}),
    ("CLI: add --json output", {"invoice/__main__.py": MAIN_V3}),
    ("Fix rounding in line_total", {"invoice/totals.py": TOTALS_V5}),
    ("Add currency formatting helper", {"invoice/totals.py": TOTALS_V6}),
    ("Add CHANGELOG", {"CHANGELOG.md": "## 0.4.0\n- bulk pricing\n- --json output\n"}),
    ("Bump version to 0.4.0", {"invoice/__init__.py": '__version__ = "0.4.0"\n'}),
    ("Tidy CLI imports", {"invoice/__main__.py": MAIN_V4 + "\n"}),
]


def build(d):
    d = Path(d)
    d.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="Rae Okafor", GIT_AUTHOR_EMAIL="rae@example.com",
               GIT_COMMITTER_NAME="Rae Okafor", GIT_COMMITTER_EMAIL="rae@example.com")

    def git(*a):
        subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main", *a],
                       cwd=d, env=env, check=True, capture_output=True)

    git("init", "-q")
    for i, (msg, files) in enumerate(COMMITS):
        for rel, text in files.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        git("add", "-A")
        stamp = f"2026-0{1 + i // 4}-{10 + i:02d}T10:00:00+00:00"
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = stamp
        git("commit", "-q", "-m", msg)


if __name__ == "__main__":
    build(sys.argv[1])
