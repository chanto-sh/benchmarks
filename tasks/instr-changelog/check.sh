#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -m unittest -q test_core 2>&1 || exit 1
cp "$HERE/hidden/check_changelog.py" ./_check_changelog.py
python3 -m unittest -q _check_changelog 2>&1; r=$?
rm -f _check_changelog.py
exit $r
