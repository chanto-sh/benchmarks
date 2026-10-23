#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_stats.py" test_stats.py || exit 1
# New tests may be added; the originals also run from a pristine copy.
cp "$HERE/files/test_stats.py" ./_original_test_stats.py
python3 -m unittest -q _original_test_stats 2>&1; r=$?
rm -f _original_test_stats.py
[ $r -eq 0 ] || exit 1
python3 -m unittest -q test_stats 2>&1 || exit 1
python3 "$HERE/hidden/check.py"
