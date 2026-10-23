#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_billing.py" test_billing.py || exit 1
# New tests may be added; the originals also run from a pristine copy.
cp "$HERE/files/test_billing.py" ./_original_test_billing.py
python3 -m unittest -q _original_test_billing 2>&1; r=$?
rm -f _original_test_billing.py
[ $r -eq 0 ] || exit 1
for f in rates.csv invoices/2026-08.csv invoices/2026-09.csv; do
  cmp -s "$HERE/files/$f" "$f" || { echo "$f was modified"; exit 1; }
done
python3 -m unittest -q test_billing 2>&1 || exit 1
TMPDIR="$(mktemp -d)"; export TMPDIR
python3 billing/run.py invoices/2026-09.csv > "$TMPDIR/_sep.txt" 2>&1
diff "$HERE/hidden/expected-09.txt" "$TMPDIR/_sep.txt" || { echo "September report differs (expected vs got above)"; exit 1; }
cp "$HERE/hidden/2026-10.csv" "$TMPDIR/_oct.csv"
cp "$HERE/hidden/rates-10.csv" "$TMPDIR/_rates10.csv"
BILLING_RATES="$TMPDIR/_rates10.csv" python3 billing/run.py "$TMPDIR/_oct.csv" > "$TMPDIR/_oct.txt" 2>&1
diff "$HERE/hidden/expected-10.txt" "$TMPDIR/_oct.txt" || { echo "hidden October report differs"; exit 1; }
python3 - <<'PY'
from billing.parse import load
import os
invs = load(os.path.join(os.environ["TMPDIR"], "_oct.csv"))
codes = [l.currency for i in invs for l in i.lines]
assert all(c == c.upper() and c == c.strip() for c in codes), codes
print("hidden ok")
PY
