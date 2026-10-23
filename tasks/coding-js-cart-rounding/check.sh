#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
cmp -s "$HERE/files/test/cart.test.js" test/cart.test.js || { echo "test/cart.test.js was modified"; exit 1; }
node --test 2>&1 || exit 1
T="$(mktemp -d)"
cp "$HERE/hidden/hidden_cart.js" "$T/hidden_cart.js"
CART_CASES="$HERE/hidden/cases.json" node --test "$T/hidden_cart.js" 2>&1; r=$?
rm -rf "$T"
exit $r
