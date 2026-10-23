#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_reports.py" test_reports.py || exit 1
# New tests may be added; the originals also run from a pristine copy.
cp "$HERE/files/test_reports.py" ./_original_test_reports.py
python3 -m unittest -q _original_test_reports 2>&1; r=$?
rm -f _original_test_reports.py
[ $r -eq 0 ] || exit 1
python3 -m unittest -q test_reports 2>&1 || exit 1
python3 "$HERE/hidden/structure.py" || exit 1
cp "$HERE/hidden/hidden_reports_check.py" ./_hidden_reports_check.py
python3 -m unittest -q _hidden_reports_check 2>&1; r=$?
rm -f _hidden_reports_check.py
exit $r
