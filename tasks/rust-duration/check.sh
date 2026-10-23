#!/bin/bash
grep -q 'assert_eq!(parse_duration("1h5m10s"), Ok(3910));' src/lib.rs || { echo "tests modified"; exit 1; }
cargo test --quiet 2>&1
