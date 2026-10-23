#!/usr/bin/env python3
"""Import a fixed sample of Aider's polyglot benchmark (Exercism exercises)
as bench tasks, so the comparison doesn't rest only on tasks written by
Chanto's author.

    python3 import_polyglot.py [--per-lang 6] [--seed 42] [--src /tmp/polyglot-benchmark] [--dest DIR]
    python3 import_polyglot.py --per-lang 999      # the whole Python/Go/Rust set

Each task gets the exercise stub, its instructions and its test files. Tests
are visible (agents normally run them), but check.sh restores the original
tests before grading, so editing them can't help. Python, Go and Rust only:
they run offline with no package installs, so every agent gets the same setup.
"""

import argparse
import json
import random
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS = ROOT / "tasks"
REPO = "https://github.com/Aider-AI/polyglot-benchmark.git"

TEST_CMD = {
    "python": "python3 -m unittest -q {tests}",
    "go": "go test ./... 2>&1",
    # Exercism marks most Rust tests #[ignore] (a teaching device); make_task
    # removes the markers so agents see every test, and the grader runs them all.
    "rust": "cargo test --quiet -- --include-ignored 2>&1",
}

PROMPT = """Solve this coding exercise. The specification is in {docs}. Implement it in {solution} \
(keep the existing function/type names and signatures). The tests in {tests} must pass; \
do not modify the tests."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="/tmp/polyglot-benchmark")
    ap.add_argument("--per-lang", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dest", default=str(TASKS), help="where to write the tasks (default tasks)")
    args = ap.parse_args()
    src = Path(args.src)
    if not src.exists():
        subprocess.run(["git", "clone", "-q", "--depth", "1", REPO, str(src)], check=True)
    rng = random.Random(args.seed)
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("poly-*"):
        shutil.rmtree(old)
    for lang in TEST_CMD:
        names = sorted(p.name for p in (src / lang / "exercises" / "practice").iterdir() if p.is_dir())
        rng.shuffle(names)
        taken = 0
        for name in names:
            if taken == args.per_lang:
                break
            ex = src / lang / "exercises" / "practice" / name
            tdir = dest / f"poly-{lang}-{name}"
            if make_task(lang, ex, tdir) and valid(tdir, ex, lang):
                taken += 1
                print(f"imported {tdir.name}")
            else:
                shutil.rmtree(tdir, ignore_errors=True)
                print(f"skipped {lang}/{name} (stub passes, or the reference solution fails the grader)")


def make_task(lang, ex, tdir):
    meta = json.loads((ex / ".meta" / "config.json").read_text())["files"]
    files = tdir / "files"
    shutil.copytree(ex, files, ignore=shutil.ignore_patterns(".meta"))
    # Docs: instructions plus any append file, in one file every agent finds.
    docs = files / ".docs"
    (files / "INSTRUCTIONS.md").write_text("\n\n".join(p.read_text() for p in sorted(docs.glob("*.md"))))
    shutil.rmtree(docs)
    if lang == "rust":
        for t in meta["test"]:
            f = files / t
            f.write_text(re.sub(r"(?m)^\s*#\[ignore\]\s*\n", "", f.read_text()))
    # Pristine copies of the tests, restored by the grader.
    for t in meta["test"] + meta.get("editor", []):
        dst = tdir / "pristine" / t
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(files / t, dst)
    test_mod = " ".join(Path(t).stem for t in meta["test"])
    (tdir / "prompt.txt").write_text(PROMPT.format(docs="INSTRUCTIONS.md", solution=", ".join(meta["solution"]), tests=", ".join(meta["test"])))
    (tdir / "check.sh").write_text("#!/bin/bash\nset -e\n" 'cp -R "$(dirname "$0")/pristine/." .\n' f"{TEST_CMD[lang].format(tests=test_mod)}\n")
    return len(meta["example"]) == 1


def grade(tdir, setup) -> bool:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        shutil.copytree(tdir / "files", d, dirs_exist_ok=True)
        setup(Path(d))
        r = subprocess.run(["bash", str(tdir / "check.sh")], cwd=d, capture_output=True, timeout=600)
        return r.returncode == 0


def valid(tdir, ex, lang) -> bool:
    """The untouched stub must fail and the reference solution must pass."""
    meta = json.loads((ex / ".meta" / "config.json").read_text())["files"]
    code = [f for f in meta["solution"] if not f.endswith((".toml", ".mod"))][0]
    example = ex / meta["example"][0]
    return not grade(tdir, lambda d: None) and grade(tdir, lambda d: shutil.copy(example, d / code))


if __name__ == "__main__":
    main()
