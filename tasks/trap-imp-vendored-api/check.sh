#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_client.py" test_client.py || exit 1
cmp -s "$HERE/files/vendor/ratelimit.py" "vendor/ratelimit.py" || { echo "vendor/ratelimit.py was modified"; exit 1; }
python3 "$HERE/hidden/check.py"
