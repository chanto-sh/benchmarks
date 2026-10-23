#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -m unittest -q test_loader 2>&1 || exit 1
cp "$HERE/hidden/check_logging.py" ./_check_logging.py
python3 -m unittest -q _check_logging 2>&1; r=$?
rm -f _check_logging.py
exit $r
