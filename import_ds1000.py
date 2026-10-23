#!/usr/bin/env python3
"""Import DS-1000 data-science problems.

    python3 import_ds1000.py [--count 30] [--seed 42] [--libraries Pandas,Numpy,Scipy]

DS-1000 (Lai et al., 2022) is 1,000 StackOverflow-style problems about pandas,
numpy, scipy, matplotlib, scikit-learn, TensorFlow and PyTorch, each with a
reference solution and a executing test. Only the `Origin` variants are sampled,
so the same problem does not appear several times under different rewrites, and
only the libraries installed for the grading interpreter are offered.

Each task gives the agent the original problem statement and a `solution.py`
stub (`result = ...`). The test lives in `pristine/` and is copied in by
`check.sh`, so it is not editable from the workspace. Every candidate is
validated: the untouched stub must fail and the reference solution must pass.
"""
import argparse
import json
import random
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS = ROOT / "tasks"
CACHE = Path.home() / ".cache/chanto-bench"
DATASET = "xlangai/DS-1000"
LIBRARIES = {
    "Pandas": "pandas",
    "Numpy": "numpy",
    "Scipy": "scipy",
    "Sklearn": "sklearn",
    "Matplotlib": "matplotlib",
    "Tensorflow": "tensorflow",
    "Pytorch": "torch",
}
CHECK = """#!/bin/bash
set -eu
cp "$(dirname "$0")/pristine/test.py" .ds1000_test.py
python3 .ds1000_test.py
"""


def dataset():
    path = CACHE / "ds1000.json"
    if not path.exists():
        rows = []
        for offset in range(0, 1000, 100):
            url = (f"https://datasets-server.huggingface.co/rows?dataset={DATASET}"
                   f"&config=default&split=test&offset={offset}&length=100")
            with urllib.request.urlopen(url, timeout=60) as response:
                rows.extend(item["row"] for item in json.load(response)["rows"])
        if len(rows) != 1000:
            raise RuntimeError(f"Expected 1000 DS-1000 problems, got {len(rows)}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows))
    return json.loads(path.read_text())


def make_task(row, dest):
    """Write one task: prompt, stub, hidden test runner and reference solution."""
    files = dest / "files"
    pristine = dest / "pristine"
    ref = dest / "ref"
    for d in (files, pristine, ref):
        d.mkdir(parents=True, exist_ok=True)
    (files / "solution.py").write_text("result = ...  # put solution in this variable\n")
    (ref / "solution.py").write_text(row["reference_code"])
    (pristine / "test.py").write_text(
        row["code_context"]
        + '\n\nwith open("solution.py") as handle:\n    test_execution(handle.read())\n'
    )
    problem = row["prompt"].rstrip()
    (dest / "prompt.txt").write_text(
        "Solve the data-science problem below. Put only the Python code that replaces "
        "the final `<code>` block in `solution.py` (it must assign `result`). "
        "`check.sh` runs hidden tests; do not modify the tests.\n\n"
        + problem + "\n"
    )
    (dest / "check.sh").write_text(CHECK)
    (dest / "check.sh").chmod(0o755)
    return f"ds1000-{row['metadata']['problem_id']}"


def grade(task):
    with tempfile.TemporaryDirectory() as workdir:
        shutil.copytree(task / "files", workdir, dirs_exist_ok=True)
        untouched = subprocess.run(["bash", str(task / "check.sh")], cwd=workdir,
                                   capture_output=True, timeout=900)
        shutil.copytree(task / "ref", workdir, dirs_exist_ok=True)
        reference = subprocess.run(["bash", str(task / "check.sh")], cwd=workdir,
                                   capture_output=True, timeout=900)
    return untouched.returncode != 0, reference.returncode == 0, reference.stderr[-600:]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--libraries", default="Pandas,Numpy,Scipy",
                    help="comma-separated DS-1000 libraries to consider")
    ap.add_argument("--dest", type=Path, default=TASKS)
    args = ap.parse_args()
    wanted = [x.strip() for x in args.libraries.split(",") if x.strip()]
    unknown = [x for x in wanted if x not in LIBRARIES]
    if unknown:
        sys.exit(f"unknown library: {', '.join(unknown)} (known: {', '.join(LIBRARIES)})")
    import importlib
    for library in wanted:
        try:
            importlib.import_module(LIBRARIES[library])
        except ImportError:
            sys.exit(f"{library} problems need the `{LIBRARIES[library]}` package")
    rows = [r for r in dataset()
            if r["metadata"]["library"] in wanted
            and r["metadata"]["perturbation_type"] == "Origin"]
    random.Random(args.seed).shuffle(rows)
    for old in args.dest.glob("ds1000-*"):
        shutil.rmtree(old)
    kept = 0
    for row in rows:
        if kept == args.count:
            break
        staging = args.dest / ".ds1000-staging"
        shutil.rmtree(staging, ignore_errors=True)
        slug = make_task(row, staging)
        untouched_fails, reference_passes, detail = grade(staging)
        if untouched_fails and reference_passes:
            final = args.dest / slug
            shutil.rmtree(final, ignore_errors=True)
            staging.rename(final)
            kept += 1
            print(f"imported {slug} ({row['metadata']['library']})", flush=True)
        else:
            shutil.rmtree(staging, ignore_errors=True)
            reason = "stub already passes" if not untouched_fails else "reference fails"
            print(f"skipped {slug} ({row['metadata']['library']}: {reason}) "
                  f"{detail.strip()[:160]}", flush=True)
    print(f"kept {kept} / {len(rows)} Origin problems", flush=True)


if __name__ == "__main__":
    main()
