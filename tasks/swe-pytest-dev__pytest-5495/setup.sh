#!/bin/bash
set -eu
exec python3 "$(cd "$(dirname "$0")/../.." && pwd)/import_swebench.py" --setup "$(dirname "$0")" --python python3.9
