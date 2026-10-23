#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_shop.py" test_shop.py || exit 1
# New tests may be added; the originals also run from a pristine copy.
cp "$HERE/files/test_shop.py" ./_original_test_shop.py
python3 -m unittest -q _original_test_shop 2>&1; r=$?
rm -f _original_test_shop.py
[ $r -eq 0 ] || exit 1
python3 -W error::DeprecationWarning -m unittest -q test_shop 2>&1 || exit 1
python3 "$HERE/hidden/no_legacy.py" || exit 1
cp "$HERE/hidden/hidden_shop_check.py" ./_hidden_shop_check.py
python3 -W error::DeprecationWarning -m unittest -q _hidden_shop_check 2>&1; r=$?
rm -f _hidden_shop_check.py
exit $r
