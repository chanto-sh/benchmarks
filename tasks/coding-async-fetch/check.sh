#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_fetcher.py" test_fetcher.py || exit 1
# New tests may be added; the originals also run from a pristine copy.
cp "$HERE/files/test_fetcher.py" ./_original_test_fetcher.py
python3 -m unittest -q _original_test_fetcher 2>&1; r=$?
rm -f _original_test_fetcher.py
[ $r -eq 0 ] || exit 1
python3 -m unittest -q test_fetcher 2>&1 || exit 1
cp "$HERE/hidden/hidden_fetcher_check.py" ./_hidden_fetcher_check.py
python3 -m unittest -q _hidden_fetcher_check 2>&1; r=$?
rm -f _hidden_fetcher_check.py
exit $r
