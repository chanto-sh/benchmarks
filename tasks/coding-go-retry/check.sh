#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
cmp -s "$HERE/files/retry_test.go" retry_test.go || { echo "retry_test.go was modified"; exit 1; }
go vet ./... 2>&1 || exit 1
go test -count=1 ./... 2>&1 || exit 1
cp "$HERE/hidden/hidden_retry_test.go" ./zz_hidden_retry_test.go
go test -count=1 -run 'TestHidden' ./... 2>&1; r=$?
rm -f zz_hidden_retry_test.go
exit $r
