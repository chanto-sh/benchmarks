#!/bin/bash
set -eu
cp "$(dirname "$0")/pristine/test.py" .ds1000_test.py
python3 .ds1000_test.py
