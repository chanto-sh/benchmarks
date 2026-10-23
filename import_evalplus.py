#!/usr/bin/env python3
"""Import HumanEval+ and MBPP+ tasks from EvalPlus.

    python3 import_evalplus.py [--per-set 30] [--seed 42] [--sets humaneval,mbpp]
    python3 import_evalplus.py --per-set 999   # every problem

EvalPlus publishes stricter tests for the OpenAI HumanEval and Google MBPP
problems. Each imported task gives the agent a stub `solution.py` and the
original problem statement; the tests are hidden in `pristine/` and restored by
`check.sh`, so editing or reading them from the workspace is not possible
(the benchmark's offline sandbox protects the repository).

The tests use numpy, so the importing interpreter must have it. Every imported
task is validated before it is kept: the untouched stub must fail and the
canonical solution must pass the hidden tests.
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
SETS = {
    "humaneval": ("evalplus/humanevalplus", 164),
    "mbpp": ("evalplus/mbppplus", 378),
}
CHECK = """#!/bin/bash
set -eu
cp "$(dirname "$0")/pristine/test.py" .evalplus_test.py
python3 .evalplus_test.py
"""


def dataset(name):
    path = CACHE / f"evalplus-{name}.json"
    if not path.exists():
        rows = []
        for offset in range(0, SETS[name][1], 100):
            url = (f"https://datasets-server.huggingface.co/rows?dataset={SETS[name][0]}"
                   f"&config=default&split=test&offset={offset}&length=100")
            with urllib.request.urlopen(url, timeout=60) as response:
                rows.extend(item["row"] for item in json.load(response)["rows"])
        if len(rows) != SETS[name][1]:
            raise RuntimeError(f"Expected {SETS[name][1]} {name} problems, got {len(rows)}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows))
    return json.loads(path.read_text())


def entry_point(row, name):
    if name == "humaneval":
        return row["entry_point"]
    match = re.search(r"(?m)^def\s+(\w+)\s*\(", row["code"])
    if not match:
        raise ValueError("no function definition in MBPP+ canonical solution")
    return match.group(1)


def signature(code):
    """The `def` header, including any continuation lines, without the body."""
    header = []
    for line in code.lstrip().splitlines():
        header.append(line)
        if line.rstrip().endswith(":"):
            return "\n".join(header)
    raise ValueError("no function signature in MBPP+ canonical solution")


def make_task(row, name, dest):
    """Write one task: stub, hidden tests, reference solution and prompt."""
    entry = entry_point(row, name)
    files = dest / "files"
    pristine = dest / "pristine"
    ref = dest / "ref"
    for d in (files, pristine, ref):
        d.mkdir(parents=True, exist_ok=True)
    if name == "humaneval":
        task_id = row["task_id"].split("/")[-1]
        stub = row["prompt"]
        solution = row["prompt"] + row["canonical_solution"]
        test = f"from solution import {entry}\n" + row["test"] + f"\ncheck({entry})\n"
        problem = (
            "Complete the Python function in `solution.py` so that it matches its docstring. "
            "`check.sh` runs hidden tests, a superset of the docstring examples; do not modify "
            "the tests."
        )
        slug = f"humaneval-{task_id}"
    else:
        stub = signature(row["code"]) + "\n    pass\n"
        solution = row["code"]
        test = "from solution import *\n" + row["test"]
        problem = (
            f"Write `{entry}` in `solution.py`: {row['prompt'].rstrip()} "
            "`check.sh` runs hidden tests; do not modify the tests."
        )
        slug = f"mbpp-{row['task_id']}"
    (files / "solution.py").write_text(stub)
    (pristine / "test.py").write_text(test)
    (ref / "solution.py").write_text(solution)
    (dest / "prompt.txt").write_text(problem + "\n")
    (dest / "check.sh").write_text(CHECK)
    (dest / "check.sh").chmod(0o755)
    return slug


def grade(task):
    """Run check.sh on the untouched files and on the reference solution."""
    with tempfile.TemporaryDirectory() as workdir:
        shutil.copytree(task / "files", workdir, dirs_exist_ok=True)
        untouched = subprocess.run(["bash", str(task / "check.sh")], cwd=workdir,
                                   capture_output=True, timeout=600)
        shutil.copytree(task / "ref", workdir, dirs_exist_ok=True)
        reference = subprocess.run(["bash", str(task / "check.sh")], cwd=workdir,
                                   capture_output=True, timeout=600)
    return untouched.returncode != 0, reference.returncode == 0, reference.stderr[-600:]


def main():
    try:
        import numpy  # noqa: F401  (the hidden tests import it)
    except ImportError:
        sys.exit("EvalPlus tests need numpy: install it for the interpreter running the tasks")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sets", default=",".join(SETS), help="comma-separated: humaneval,mbpp")
    ap.add_argument("--per-set", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dest", type=Path, default=TASKS)
    args = ap.parse_args()
    unknown = [s for s in args.sets.split(",") if s not in SETS]
    if unknown:
        sys.exit(f"unknown set(s): {', '.join(unknown)} (known: {', '.join(SETS)})")
    rng = random.Random(args.seed)
    for name in args.sets.split(","):
        for old in args.dest.glob(("humaneval-" if name == "humaneval" else "mbpp-") + "*"):
            shutil.rmtree(old)
        rows = sorted(dataset(name), key=lambda r: str(r["task_id"]))
        rng.shuffle(rows)
        kept = 0
        for row in rows:
            if kept == args.per_set:
                break
            staging = args.dest / ".evalplus-staging"
            shutil.rmtree(staging, ignore_errors=True)
            slug = make_task(row, name, staging)
            untouched_fails, reference_passes, detail = grade(staging)
            if untouched_fails and reference_passes:
                final = args.dest / slug
                shutil.rmtree(final, ignore_errors=True)
                staging.rename(final)
                kept += 1
                print(f"imported {slug}")
            else:
                shutil.rmtree(staging, ignore_errors=True)
                reason = "stub already passes" if not untouched_fails else "reference fails"
                print(f"skipped {slug} ({reason}) {detail.strip()[:160]}")
        print(f"{name}: kept {kept} / {len(rows)}")


if __name__ == "__main__":
    main()
