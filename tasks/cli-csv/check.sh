#!/bin/bash
out=$(python3 report.py 2>&1)
expected=$'South: 207.50\nNorth: 125.00\nEast: 20.00\nWest: 2.50'
[ "$out" = "$expected" ] && echo ok || { echo "got:"; echo "$out"; exit 1; }
