#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_sessions.py" test_sessions.py || exit 1
# New tests may be added; the originals also run from a pristine copy.
cp "$HERE/files/test_sessions.py" ./_original_test_sessions.py
python3 -m unittest -q _original_test_sessions 2>&1; r=$?
rm -f _original_test_sessions.py
[ $r -eq 0 ] || exit 1
python3 -m unittest -q test_sessions 2>&1 || exit 1
python3 "$HERE/hidden/perf_check.py" "$HERE/hidden"
