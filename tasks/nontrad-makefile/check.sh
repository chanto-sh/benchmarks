#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
for f in data/store_north.csv data/store_south.csv test/test_summarize.py test/fixtures/one.csv; do
  cmp -s "$HERE/files/$f" "$f" || { echo "$f was modified"; exit 1; }
done
[ -f Makefile ] || { echo "Makefile missing"; exit 1; }
python3 "$HERE/hidden/verify.py" "$PWD" "$HERE/files"
