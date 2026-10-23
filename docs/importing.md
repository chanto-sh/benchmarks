# Imported datasets

Each importer samples problems with a fixed seed and keeps a problem only after
validating it locally: the untouched starting point must fail the hidden check
and the reference solution must pass. Package versions differ between machines,
so run the importer on the machine that runs the benchmark. Licenses are in
[NOTICE.md](../NOTICE.md).

## SWE-bench Lite and Verified (`swe-*`)

```sh
nice -n 19 python3 import_swebench.py --count 25 --seed 42
# Recreate and revalidate the committed selections:
nice -n 19 python3 import_swebench.py --ids swebench-selection.json
nice -n 19 python3 import_swebench.py --dataset verified --ids swebench-verified-selection.json
```

`--dataset lite` (the default) samples the 300-instance test split of
[SWE-bench Lite](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite);
`--dataset verified` samples the 500-instance
[SWE-bench Verified](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified).
Candidates come from pytest, requests, Flask and pylint; heavier repositories
are left out.

Importing needs git, Python with venv and pip, and network access to Hugging
Face, GitHub and PyPI. No Docker. Python 3.9 suits the older repositories and
3.11 the Flask case with a `tomllib` test; the importer prefers those when
installed (`--python` overrides).

Each task gets its own checkout at `base_commit` and a fresh `.venv` with the
repository installed in editable mode, from known requirements rather than the
upstream setup scripts. A candidate is kept only if its tests fail on the base
and pass with the gold patch, within ten minutes for setup and both checks.
Collection errors, timeouts, empty runs and skipped gold tests are rejected.
Gold patches are used only in temporary validation folders, never in tasks.

Grading restores the base tests, applies the official test patch and runs
`FAIL_TO_PASS` plus `PASS_TO_PASS`. Agents get only the problem statement and an
instruction to fix the issue and run the relevant tests.

The committed Lite selection is **25 tasks** (16 pytest, 5 pylint, 3 Flask,
1 requests); the Verified selection adds **27** (16 pytest, 5 pylint,
5 requests, 1 Flask). Validation summaries are in `swebench-validation.json` and
`swebench-verified-validation.json`. Datasets, bare clones and logs are cached in
`~/.cache/chanto-bench/`.

## EvalPlus: HumanEval+ and MBPP+ (`humaneval-*`, `mbpp-*`)

```sh
python3 import_evalplus.py --per-set 30 --seed 42
python3 import_evalplus.py --per-set 999      # every problem
```

From [HumanEval+](https://huggingface.co/datasets/evalplus/humanevalplus)
(164 problems) and [MBPP+](https://huggingface.co/datasets/evalplus/mbppplus)
(378), which keep the original problems and add tests that catch overfitted
solutions. The agent gets `solution.py` with an empty body and the problem
statement; the official tests stay in `pristine/`, outside the workspace, and
are copied in at grading. The tests need numpy for the grading interpreter. The
committed selection is 30 of each (seed 42).

## DS-1000 (`ds1000-*`)

```sh
python3 import_ds1000.py --count 30 --seed 42
python3 import_ds1000.py --libraries Pandas,Numpy,Scipy,Sklearn --count 40
```

[DS-1000](https://github.com/xlang-ai/DS-1000) is 1,000 StackOverflow-style
data-science problems. Only the original variants are sampled, from libraries
installed for the grading interpreter (Pandas, Numpy and Scipy by default). The
agent gets the problem and a `result = ...` stub; the test runner stays in
`pristine/`. Problems broken by newer library versions are skipped. The
committed selection is 30 tasks (seed 42).

## FinQA (`finqa-*`, showcase)

```sh
python3 import_finqa.py --count 20 --per-task 5 --seed 42
python3 run.py --tier showcase --tasks 'finqa-*'
```

[FinQA](https://github.com/czyssrs/FinQA) asks questions about tables from real
company filings. Each task bundles five questions with their tables and asks for
`answers.json`. Only objectively graded answers are kept (numbers, percentages,
yes/no). Grading allows for commas, currency signs, percentages and a small
numeric tolerance. This is our own answer check, not FinQA's program-execution
metric. The committed selection is 20 tasks.

## Aider's polyglot set (`poly-*`)

```sh
python3 import_polyglot.py --per-lang 6 --seed 42
python3 import_polyglot.py --per-lang 999      # the whole Python/Go/Rust set
```

Exercism exercises in Python, Go and Rust, as selected by
[Aider's polyglot benchmark](https://github.com/Aider-AI/polyglot-benchmark).
