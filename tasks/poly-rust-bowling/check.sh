#!/bin/bash
set -e
cp -R "$(dirname "$0")/pristine/." .
cargo test --quiet -- --include-ignored 2>&1
