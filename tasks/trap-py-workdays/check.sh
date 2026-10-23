#!/bin/bash
set -e
[ "$(shasum test_workdays.py | cut -c1-12)" = "$TEST_SHA" ] || { echo "tests were modified"; exit 1; }
python3 -m unittest -q test_workdays 2>&1
python3 - <<'PY'
from datetime import date
from workdays import business_days as b
assert b(date(2026, 10, 1), date(2026, 11, 2)) == 22, b(date(2026, 10, 1), date(2026, 11, 2))
assert b(date(2026, 10, 1), date(2026, 11, 2), holidays={date(2026, 10, 12), date(2026, 10, 31)}) == 21
assert b(date(2026, 10, 10), date(2026, 10, 12)) == 0
assert b(date(2026, 11, 2), date(2026, 10, 1)) == -22
print("hidden ok")
PY
