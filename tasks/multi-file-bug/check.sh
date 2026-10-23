#!/bin/bash
python3 -m unittest -q test_app 2>&1 || exit 1
python3 -c '
from app.utils.merge import merge
b={"a":{"b":{"c":1,"d":2}},"x":1}
o={"a":{"b":{"c":9}}}
r=merge(b,o)
assert r=={"a":{"b":{"c":9,"d":2}},"x":1}, r
assert b=={"a":{"b":{"c":1,"d":2}},"x":1}, "base mutated"
assert merge({"a":{"b":1}},{"a":5})=={"a":5}
print("hidden ok")'
