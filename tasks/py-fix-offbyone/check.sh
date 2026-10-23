#!/bin/bash
set -e
[ "$(shasum test_stats.py | cut -c1-12)" = "$TEST_SHA" ] || { echo "tests were modified"; exit 1; }
python3 -m unittest -q test_stats 2>&1
