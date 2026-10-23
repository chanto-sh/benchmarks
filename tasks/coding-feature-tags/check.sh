#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
# The task asks for new tests: the original ones must stay as they were, and
# also run from a pristine copy so weakening one can't make the code pass.
python3 "$HERE/../../keep_tests.py" "$HERE/files/test_notes.py" test_notes.py || exit 1
cp "$HERE/files/test_notes.py" ./_original_test_notes.py
python3 -m unittest -q _original_test_notes 2>&1; r=$?
rm -f _original_test_notes.py
[ $r -eq 0 ] || exit 1
python3 -m unittest -q test_notes 2>&1 || exit 1
cp "$HERE/hidden/hidden_tags_check.py" ./_hidden_tags_check.py
python3 -m unittest -q _hidden_tags_check 2>&1; r=$?
rm -f _hidden_tags_check.py
exit $r
