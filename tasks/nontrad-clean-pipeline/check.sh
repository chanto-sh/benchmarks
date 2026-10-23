#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -f clean.py ] || { echo "clean.py missing"; exit 1; }
cmp -s "$HERE/files/country_aliases.csv" country_aliases.csv || { echo "country_aliases.csv was modified"; exit 1; }
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT
status=0
for name in sample full; do
  if [ $name = sample ]; then in="$HERE/files/raw/customers_sample.csv"; else in="$HERE/hidden/customers_full.csv"; fi
  # A copy of the input outside the workspace, so nothing can be precomputed.
  cp "$in" "$out/in_$name.csv"
  python3 clean.py "$out/in_$name.csv" "$out/out_$name.csv" || { echo "clean.py failed on the $name export"; status=1; continue; }
  if cmp -s "$HERE/hidden/expected_$name.csv" "$out/out_$name.csv"; then
    echo "$name: ok"
  else
    echo "$name: output differs from expected:"
    diff "$HERE/hidden/expected_$name.csv" "$out/out_$name.csv" | head -12
    status=1
  fi
done
exit $status
