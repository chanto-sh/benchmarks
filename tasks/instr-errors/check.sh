#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -m unittest -q test_book 2>&1 || exit 1
cp "$HERE/hidden/check_errors.py" ./_check_errors.py
python3 -m unittest -q _check_errors 2>&1; r=$?
rm -f _check_errors.py
exit $r
