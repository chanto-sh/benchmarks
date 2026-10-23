"""Tiny lint: no tabs, no trailing whitespace, no print() in library code."""
import pathlib
import sys

bad = 0
for p in sorted(pathlib.Path(sys.argv[1]).rglob("*.py")):
    if p.name.startswith("_build_info"):
        continue
    for i, line in enumerate(p.read_text().splitlines(), 1):
        if "\t" in line or line != line.rstrip() or line.lstrip().startswith("print("):
            print(f"{p}:{i}: lint error")
            bad += 1
print(f"lint: {bad} problem(s)")
sys.exit(1 if bad else 0)
