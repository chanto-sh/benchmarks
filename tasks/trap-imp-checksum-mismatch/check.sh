#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_verify.py" test_verify.py || exit 1
cmp -s "$HERE/files/SHA256SUMS" "SHA256SUMS" || { echo "SHA256SUMS was modified"; exit 1; }
cmp -s "$HERE/files/artifacts/cli-2.0.1.zip" "artifacts/cli-2.0.1.zip" || { echo "artifacts/cli-2.0.1.zip was modified"; exit 1; }
cmp -s "$HERE/files/artifacts/docs-2026.10.tar.gz" "artifacts/docs-2026.10.tar.gz" || { echo "artifacts/docs-2026.10.tar.gz was modified"; exit 1; }
cmp -s "$HERE/files/artifacts/libfoo-1.4.2.tar.gz" "artifacts/libfoo-1.4.2.tar.gz" || { echo "artifacts/libfoo-1.4.2.tar.gz was modified"; exit 1; }
python3 "$HERE/hidden/check.py"
