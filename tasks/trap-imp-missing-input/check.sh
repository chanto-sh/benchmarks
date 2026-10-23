#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_reconcile.py" test_reconcile.py || exit 1
cmp -s "$HERE/files/exports/ledger_2026-08.csv" "exports/ledger_2026-08.csv" || { echo "exports/ledger_2026-08.csv was modified"; exit 1; }
cmp -s "$HERE/files/exports/bank_2026-08.csv" "exports/bank_2026-08.csv" || { echo "exports/bank_2026-08.csv was modified"; exit 1; }
cmp -s "$HERE/files/exports/bank_2026-09.csv" "exports/bank_2026-09.csv" || { echo "exports/bank_2026-09.csv was modified"; exit 1; }
python3 "$HERE/hidden/check.py"
