#!/bin/bash
# Runs the agent's .ci/pipeline.yml against pristine copies of everything else.
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -f .ci/pipeline.yml ] || { echo "pipeline missing"; exit 1; }
python3 "$HERE/hidden/runner.py" .ci/pipeline.yml "$HERE/files"
