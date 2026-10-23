#!/bin/bash
set -e
[ "$(shasum test_csvline.py | cut -c1-12)" = "$TEST_SHA" ] || { echo "tests were modified"; exit 1; }
python3 -m unittest -q test_csvline 2>&1
python3 - <<'PY'
from csvline import split_csv_line as s
assert s("") == [""], s("")
assert s('"a""b""c"') == ['a"b"c'], s('"a""b""c"')
assert s('1,"2,3,4",5') == ["1", "2,3,4", "5"]
assert s('a,"",b') == ["a", "", "b"]
assert s(',') == ["", ""]
print("hidden ok")
PY
