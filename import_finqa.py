#!/usr/bin/env python3
"""Import FinQA financial table questions.

    python3 import_finqa.py [--count 20] [--per-task 5] [--seed 42]

FinQA (Chen et al., EMNLP 2021) asks questions over tables extracted from real
financial filings (10-Ks), with a numeric answer for each. This importer bundles
several examples per task: the agent gets `questions.json` (question, table and
surrounding filing text) and writes `answers.json` mapping each id to its
answer. Free-text answers, which the dataset does not grade objectively, are
excluded; numeric, percentage and yes/no answers are kept.

Grading normalizes commas, currency signs, percentages and a small numeric
tolerance (see `pristine/check.py`). It is our own answer check around the
public dataset, not FinQA's program-execution metric: the tasks test reading a
financial table and computing the answer, not producing a FinQA program.
"""
import argparse
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS = ROOT / "tasks"
CACHE = Path.home() / ".cache/chanto-bench"
DATASET = "dreamerdeo/finqa"
NUMBER = re.compile(r"-?[\d,]+(?:\.\d+)?%?")
CHECK = """#!/bin/bash
set -eu
python3 "$(dirname "$0")/pristine/check.py"
"""

CHECK_PY = '''#!/usr/bin/env python3
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
    print("\\n".join(wrong))
    sys.exit(f"{len(wrong)} of {len(gold)} answers are missing or wrong")
print(f"{len(gold)} answers correct")
'''


def dataset():
    path = CACHE / "finqa.json"
    if not path.exists():
        rows = []
        for offset in range(0, 1147, 100):
            url = (f"https://datasets-server.huggingface.co/rows?dataset={DATASET}"
                   f"&config=default&split=test&offset={offset}&length=100")
            with urllib.request.urlopen(url, timeout=90) as response:
                rows.extend(item["row"] for item in json.load(response)["rows"])
        if len(rows) != 1147:
            raise RuntimeError(f"Expected 1147 FinQA test examples, got {len(rows)}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows))
    return json.loads(path.read_text())


def gradable(row):
    answer = row["answer"].strip()
    return bool(answer) and (bool(NUMBER.fullmatch(answer)) or answer.lower() in ("yes", "no"))


def make_task(rows, dest):
    files, pristine, ref = dest / "files", dest / "pristine", dest / "ref"
    for d in (files, pristine, ref):
        d.mkdir(parents=True, exist_ok=True)
    questions = []
    gold = {}
    for row in rows:
        questions.append({
            "id": row["id"],
            "question": row["question"],
            "table": row["table"],
            "context": "\n".join(row["pre_text"] + row["post_text"]),
        })
        gold[row["id"]] = row["answer"]
    (files / "questions.json").write_text(json.dumps(questions, indent=2) + "\n")
    (pristine / "gold.json").write_text(json.dumps(gold, indent=2) + "\n")
    (pristine / "check.py").write_text(CHECK_PY)
    (ref / "answers.json").write_text(json.dumps(gold, indent=2) + "\n")
    (dest / "prompt.txt").write_text(
        "Answer the financial questions in `questions.json`. Each item has a question, a "
        "table from a company filing and the surrounding text. Compute the answer from the "
        "table (the filing text explains units and definitions) and write `answers.json`, an "
        "object mapping each id to its final answer. Answers are compared numerically, so "
        "`14`, `14.0`, and `14%` are all accepted for a percentage; yes/no answers are "
        "compared case-insensitively.\n"
    )
    (dest / "check.sh").write_text(CHECK)
    (dest / "check.sh").chmod(0o755)
    return "finqa-" + str(rows[0]["id"]).replace("/", "_").replace(".", "_")[:60]


def grade(task):
    with tempfile.TemporaryDirectory() as workdir:
        shutil.copytree(task / "files", workdir, dirs_exist_ok=True)
        untouched = subprocess.run(["bash", str(task / "check.sh")], cwd=workdir,
                                   capture_output=True, timeout=300)
        shutil.copytree(task / "ref", workdir, dirs_exist_ok=True)
        reference = subprocess.run(["bash", str(task / "check.sh")], cwd=workdir,
                                   capture_output=True, timeout=300)
    return untouched.returncode != 0, reference.returncode == 0, reference.stderr[-600:]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--per-task", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dest", type=Path, default=TASKS)
    args = ap.parse_args()
    rows = sorted((r for r in dataset() if gradable(r)), key=lambda r: r["id"])
    random.Random(args.seed).shuffle(rows)
    for old in args.dest.glob("finqa-*"):
        shutil.rmtree(old)
    kept = 0
    for index in range(0, args.count * args.per_task, args.per_task):
        batch = rows[index:index + args.per_task]
        if len(batch) < args.per_task:
            break
        staging = args.dest / ".finqa-staging"
        shutil.rmtree(staging, ignore_errors=True)
        slug = make_task(batch, staging)
        untouched_fails, reference_passes, detail = grade(staging)
        if untouched_fails and reference_passes:
            final = args.dest / slug
            shutil.rmtree(final, ignore_errors=True)
            staging.rename(final)
            kept += 1
            print(f"imported {slug}", flush=True)
        else:
            shutil.rmtree(staging, ignore_errors=True)
            print(f"skipped {slug}: {detail.strip()[:160]}", flush=True)
    print(f"kept {kept} tasks of {args.per_task} questions", flush=True)


if __name__ == "__main__":
    main()
