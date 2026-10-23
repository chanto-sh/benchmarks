#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/hidden/verify.py" "$PWD" "$HERE/files"
