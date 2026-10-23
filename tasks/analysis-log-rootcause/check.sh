#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -B "$HERE/hidden/check.py"
