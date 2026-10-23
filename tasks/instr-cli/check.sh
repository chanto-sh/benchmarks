#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -m unittest -q test_cli 2>&1 || exit 1
cp "$HERE/hidden/check_cli.py" ./_check_cli.py
python3 -m unittest -q _check_cli 2>&1; r=$?
rm -f _check_cli.py
exit $r
