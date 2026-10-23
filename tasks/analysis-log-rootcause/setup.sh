#!/bin/bash
set -e
python3 "$(cd "$(dirname "$0")" && pwd)/hidden/gen.py" .
