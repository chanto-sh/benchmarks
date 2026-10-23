#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_stats_stream.py" test_stats_stream.py || exit 1
python3 "$HERE/hidden/check.py"
