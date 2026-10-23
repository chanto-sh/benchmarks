#!/bin/bash
set -eu
cp "$(dirname "$0")/pristine/test.py" .evalplus_test.py
python3 .evalplus_test.py
