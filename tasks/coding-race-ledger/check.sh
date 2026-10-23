#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_ledger.py" test_ledger.py || exit 1
# New tests may be added; the originals also run from a pristine copy.
cp "$HERE/files/test_ledger.py" ./_original_test_ledger.py
python3 -m unittest -q _original_test_ledger 2>&1; r=$?
rm -f _original_test_ledger.py
[ $r -eq 0 ] || exit 1
python3 -m unittest -q test_ledger 2>&1 || exit 1
python3 "$HERE/hidden/stress.py"
