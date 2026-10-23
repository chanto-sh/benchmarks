#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_migrations.py" test_migrations.py || exit 1
cmp -s "$HERE/files/fixtures/prod_snapshot.sql" "fixtures/prod_snapshot.sql" || { echo "fixtures/prod_snapshot.sql was modified"; exit 1; }
cmp -s "$HERE/files/migrations/001_users.sql" "migrations/001_users.sql" || { echo "migrations/001_users.sql was modified"; exit 1; }
python3 "$HERE/hidden/check.py"
