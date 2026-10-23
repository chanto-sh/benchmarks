#!/bin/bash
[ -f test_roman.py ] || { echo "no tests"; exit 1; }
python3 -m unittest -q test_roman 2>&1 || { echo "tests fail on correct impl"; exit 1; }
cp roman.py /tmp/_roman_orig.py
fail=0
# Mutant 1: missing subtractive 900. Mutant 2: off-by-one range. Mutant 3: 4 -> IIII
python3 - <<'PY'
import re
src = open("roman.py").read()
open("/tmp/_m1.py","w").write(src.replace('(900, "CM"), ', ''))
open("/tmp/_m2.py","w").write(src.replace('1 <= n <= 3999', '0 <= n <= 4000'))
open("/tmp/_m3.py","w").write(src.replace('(4, "IV"), ', ''))
PY
killed=0
for m in 1 2 3; do
  cp /tmp/_m$m.py roman.py
  if ! python3 -m unittest -q test_roman >/dev/null 2>&1; then killed=$((killed+1)); fi
done
cp /tmp/_roman_orig.py roman.py
echo "mutants killed: $killed/3"
[ $killed -eq 3 ]
