#!/usr/bin/env python3
"""Compare answers.json with the gold answers, allowing formatting differences."""
import json
import re
import sys
from pathlib import Path

gold = json.loads((Path(__file__).resolve().parent / "gold.json").read_text())
try:
    got = json.loads(Path("answers.json").read_text())
except Exception as exc:
    sys.exit(f"answers.json is missing or not valid JSON: {exc}")
if not isinstance(got, dict):
    sys.exit("answers.json must be an object mapping each id to an answer")


def number(text):
    text = str(text).strip().replace(",", "").replace("$", "").strip()
    percent = text.endswith("%")
    text = text.rstrip("%").strip()
    try:
        return float(text), percent
    except ValueError:
        return None


def same(expected, actual):
    expected, actual = str(expected).strip(), str(actual).strip()
    if expected.lower() == actual.lower():
        return True
    left, right = number(expected), number(actual)
    if left and right:
        want, got = left[0], right[0]
        candidates = [got]
        if right[1] != left[1]:
            candidates.append(got / 100 if right[1] else got * 100)
        return any(abs(want - value) <= max(1e-4, abs(want) * 1e-4) for value in candidates)
    return " ".join(expected.lower().split()) == " ".join(actual.lower().split())


wrong = []
for key, expected in gold.items():
    if key not in got:
        wrong.append(f"{key}: missing")
    elif not same(expected, got[key]):
        wrong.append(f"{key}: expected {expected!r}, got {got[key]!r}")
if wrong:
    print("\n".join(wrong))
    sys.exit(f"{len(wrong)} of {len(gold)} answers are missing or wrong")
print(f"{len(gold)} answers correct")
