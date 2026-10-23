# Chanto benchmarks

The benchmark suite for [Chanto](https://github.com/chanto-sh/chanto): coding
tasks with automated checks, a runner that drives Chanto and other coding agents
on the same model, and every raw result behind the published numbers.

- **[RESULTS.md](RESULTS.md)**: the latest results, per-task numbers, methods and caveats.
- **[AUDIT.md](AUDIT.md)**: what each run records, and how to check a result yourself.

## Running it

Clone this repository next to a Chanto checkout and build Chanto's release binary;
the runner looks for it in `../chanto` (`CHANTO_REPO` or `BENCH_CHANTO_BIN` point
elsewhere):

```sh
git clone https://github.com/chanto-sh/chanto.git
git clone https://github.com/chanto-sh/benchmarks.git chanto-benchmarks
(cd chanto && cargo build --release)
cd chanto-benchmarks

python3 run.py --agents chanto,opencode,claude --model qwen3.8-bench   # local model (Ollama)
./proxy.sh deepseek/deepseek-flash      # or a hosted model, in another terminal:
python3 run.py --api http://localhost:4000 --agents chanto,opencode,claude,codex --tier hard
```

Agents run in a sandbox (`--offline`) that hides this repository, the Chanto
sources and package caches from them, so they can't read the hidden tests or
earlier runs. `python3 -m unittest -v test_run` tests the runner itself.

## License

The runner, scripts and the tasks written for this repository are under the
[Apache License 2.0](LICENSE). Tasks imported from public benchmarks keep their
upstream licenses, among them MIT, Apache-2.0, CC BY-SA 4.0 (DS-1000) and
GPL-2.0-or-later (the pylint tasks). [NOTICE.md](NOTICE.md) lists each source.

## Tasks

Tasks in `tasks/<name>/` have `prompt.txt`, `files/`, and `check.sh` (zero means
solved). An optional `setup.sh` runs in the fresh work directory before repository
snapshotting and before the agent timer starts. Existing tasks need no hook.
Optional `env` entries are exported to grading. Task selectors accept comma-separated
names or shell globs; quote globs to keep the shell from expanding them.

Tasks fall in tiers by name: `core` (`poly-*`, `humaneval-*`, `mbpp-*`,
`trap-*`: small katas, a ceiling check), `hard` (`swe-*`: real GitHub issues
from SWE-bench Lite and Verified, where models diverge), `beyond` (`coding-*`,
`math-*`, `physics-*`, `trap-imp-*`; see below), the opt-in `showcase` (`data-*`,
`analysis-*`, `nontrad-*`, `finqa-*`) and `medium` (everything else, including
`ds1000-*` data-science problems). The default run is the four coding tiers;
`--tier showcase` (or `--tier core,showcase`) adds the rest. `--tier core,hard`
narrows a run; `--estimate` prints the projected tokens, cost and wall time from
earlier results (`results/*.json`, or `--estimate-ref`) and runs nothing.

The core and hard bands include tasks imported from public benchmarks —
[Aider's polyglot benchmark](https://github.com/Aider-AI/polyglot-benchmark),
[SWE-bench](https://github.com/SWE-bench/SWE-bench) Lite and Verified, and
[EvalPlus](https://github.com/evalplus/evalplus) — so the comparison does not
rest only on tasks written for this repository. Two adjacent-domain sets come
from public data-science and finance benchmarks: [DS-1000](https://github.com/xlang-ai/DS-1000)
data-science problems in the default (medium) run, and
[FinQA](https://github.com/czyssrs/FinQA) financial-table questions in the
opt-in showcase run. The rest of the suite adds hand-written tasks aimed at
honesty (faked "done", hardcoding, editing tests) and at shapes public
benchmarks don't cover.

## Beyond and showcase tiers

The benchmark is about coding. These tasks add honesty to it: each one is
graded by a deterministic check (no LLM grading) that calls the agent's code
with hidden parameters and inputs, so hardcoding the visible example, recalling
a half-remembered number or editing the tests fails. Checks also compare
visible tests against the originals by content. An agent that says it's done
on a failing task is counted in the report's *false "done"* column, which is
the main thing these tiers measure besides correctness. That column reads what
the agent reported about itself — the `is_error` field in Chanto's and
claude's result JSON, forge's `ERROR:` lines — not its exit code: most agents
exit 0 whatever happened, and some pass with a non-zero status. An agent that
prints no such signal shows `—` there, with the weaker exit-code proxy in the
*clean-exit fails* column beside it; agents that reported an error land in
*errored* instead.

- `coding-*` (beyond): everyday engineering in a small existing app: multi-file
  features, debugging from a failing test or stack trace, refactors that keep
  the suite green, a performance fix with a timing bound, a concurrency bug, an
  API migration.
- `math-*` (beyond): write or fix a solver whose results must be computed, not
  recalled: exact rational/big-integer results, quadrature to 1e-9, counting
  checked by brute force, exact linear algebra, a probability problem with a
  twist, numerical stability, a property that must hold on random inputs.
- `physics-*` (beyond): write or fix simulation code checked against invariants
  and references with hidden parameters: energy drift (needs a symplectic
  integrator), drag, resonance, CFL stability, orbital periods, Ising trends,
  units bugs.
- `trap-imp-*` (beyond): coding tasks that can't be done as asked
  (contradictory tests, an API that doesn't exist, a missing input, a test
  asserting a false fact, a speedup with a hidden requirement). Passing means
  doing any part that is possible and writing `BLOCKED.md` naming the real
  cause, with tests untouched and nothing faked.
- `data-*`, `analysis-*`, `nontrad-*`, `finqa-*` (showcase): exact answers over
  CSV, SQLite, JSON and financial tables (some questions are unanswerable and
  must be answered "not in data"), root causes in a large generated log or a git
  history with a decoy, layered config analysis, CI/Makefile/Dockerfile repair,
  a migration doc checked for facts from the repository, a data-cleaning
  pipeline. They produce answers rather than code, so `--report` totals them
  separately and
  never mixes them into the coding score or the paired comparison.

Each of these tasks ships a reference solution (`ref/`, an overlay on the
starting files) and wrong ones (`wrong/<name>/`: plausible mistakes,
hallucinated answers, hardcoded or test-editing fakes), kept next to
`check.sh` and outside the agent's workspace. `_OUTPUT.txt` in an overlay
stands in for the agent's captured output and `_DELETE` lists files to remove.
`python3 validate_tasks.py ['math-*,trap-imp-*']` checks every task
without a model: the untouched workspace and every wrong overlay must fail,
and the reference must pass.

## Offline runs and timeouts

```sh
python3 run.py --offline --agents chanto --tasks 'swe-*'
python3 -m unittest discover -s bench -p 'test_run.py'
# Opt-in smoke test of the real macOS sandbox (no model needed):
BENCH_SANDBOX_SMOKE=1 python3 -m unittest discover -s bench -p 'test_run.py'
```

`--offline` requires macOS `sandbox-exec`; unsupported platforms are rejected
before task setup. The sandbox applies only to the agent invocation and its
children, not import, setup, or grading. It blocks outbound IP connections except
localhost (for Ollama or a local hosted-model proxy/meter); Unix sockets remain
allowed. A local proxy can still call a hosted provider on the agent's behalf.

Agents cannot read file contents or write beneath this repository,
`~/.cache/chanto-bench/`, `~/.local/share/chanto-bench/runs/`,
`~/.local/share/chanto-bench/codex/`, or the work root (`BENCH_WORK`, default
`~/.local/share/chanto-bench/work`). Only the current task workspace and the
agent's config home are exempted inside these protected trees. The resolved
Chanto executable (including `BENCH_CHANTO_BIN`) gets an exact-file read-only
exception, not access to its containing directory. Quotes and backslashes in
paths are escaped in the sandbox profile. Other filesystem locations are not
restricted: this is benchmark answer isolation, not a general security boundary.
Chanto's nested sandbox is temporarily disabled during offline invocation;
its previous config is restored afterward, including on timeout or launch error.
Runs sharing the same work/config home should not run concurrently.

Agent, setup, and grading subprocesses run in new process groups. The runner
kills remaining children in the original group after both normal exit and
timeout, before grading agent changes. Detached children that create a new
session or process group are **not** covered by this cleanup. Grading timeouts
return exit code 124 and a timeout diagnostic; agent timeouts record
`timed_out: true` and `exit_code: -1`. Every result JSON records a top-level
`offline` boolean, including files saved when provider budget is exhausted.

## SWE-bench Lite and Verified

`--dataset lite` (the default) imports SWE-bench Lite; `--dataset verified`
imports SWE-bench Verified, the 500-instance human-validated set. Both use the
same four repositories (pytest, requests, Flask, pylint) and environment
recipes, and both are validated the same way.

Import requires git, a Python interpreter with venv/pip, and network access to
Hugging Face, GitHub, and PyPI. No Docker or dataset libraries are needed. Python
3.9 is recommended for the older repositories, and Python 3.11 for the Flask
TOML case (which has a `tomllib` regression test). The importer prefers those interpreters
when installed, otherwise its own interpreter. Override with `--python`.

```sh
nice -n 19 python3 import_swebench.py --count 25 --seed 42
# Recreate and revalidate the committed selections:
nice -n 19 python3 import_swebench.py --ids swebench-selection.json
nice -n 19 python3 import_swebench.py --dataset verified \
    --ids swebench-verified-selection.json
# Run the committed tasks directly (the importer never runs agents):
nice -n 19 python3 run.py --tasks 'swe-*' --agents chanto,opencode,claude
```

The importer downloads the **test** split of
[princeton-nlp/SWE-bench_Lite](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite)
(300 instances) or, with `--dataset verified`,
[princeton-nlp/SWE-bench_Verified](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified)
(500 instances) with standard-library HTTP and samples a sorted candidate list
with seed 42. The test split has no marshmallow, pydicom, sqlfluff, or pvlib
instances. Candidates are pytest, requests, Flask, and pylint; heavyweight
repositories are excluded. Lite restricts requests to the one instance whose
generic environment validated; Verified tries all of them and keeps the ones
that pass. Older parameterized test IDs in the dataset are sometimes truncated;
grading runs the entire corresponding test function, including all parameter
variants. Recognizable progress-bar fragments erroneously listed as tests by
the upstream parser are discarded; the original lists remain in task metadata.

Dataset JSON, bare repository clones (`repos/`), and validation logs are cached
under `~/.cache/chanto-bench/`. Each setup makes an independent checkout at
`base_commit` and a fresh `.venv`, installs compatibility dependencies and the
repository in editable mode. Dependency recipes use known requirements rather
than Docker or the upstream environment setup scripts. Source and test files
come from the base commit, never from `environment_setup_commit`. The latter is
retained in metadata for traceability. Pip's download cache is reused.

Each candidate must produce a test failure (or a pytest failure-reporter crash) on the base and pass with
the gold patch, within ten minutes including setup and both checks. Each validation check also has a 120-second
limit. Collection
errors, timeouts, empty runs, and skipped gold tests are rejected. The importer
prints a summary table, writes `swebench-selection.json` (Lite) or
`swebench-verified-selection.json` (Verified), and saves detailed results in the
cache. Failed task directories are removed. Gold patches are
used only in temporary validation directories, never placed in agent tasks.
Grading restores the base tests/fixtures, applies the official test patch, and
runs the union of `FAIL_TO_PASS` and `PASS_TO_PASS`. Agents receive only the
problem statement and the instruction to fix the issue and run relevant tests.

SWE tasks default to 1800 seconds of agent time and 600 seconds for grading;
`--timeout` overrides agent time. Setup has a separate 600-second limit and is
excluded from reported agent time. The runner places the task venv on the agent's
PATH. Import/setup/check subprocesses use `nice -n 19` to limit contention.
Installed package versions and platform differences can affect historical tasks;
reimporting always validates the selection locally rather than trusting results
from another machine. No agent runs are needed to validate tasks.

The committed Lite selection contains **25 validated tasks**: 16 pytest, 5 pylint,
3 Flask, and 1 requests. The committed Verified selection adds **27 validated
tasks** from the same four repositories: 16 pytest, 5 pylint, 5 requests, and 1
Flask. Every untouched base failed and every gold patch passed; setup plus both
checks took 8.8–75.7 seconds per accepted Lite instance on macOS. Seven Verified
candidates were rejected because the base did not produce a test failure or the
gold patch still failed grading. `pytest-dev__pytest-11148` and
`pylint-dev__pylint-7114` were rejected from Lite for the same reason. The
summaries are recorded in `swebench-validation.json` and
`swebench-verified-validation.json`; full stdout/stderr remains in the cache.
Task directories contain only small prompts, metadata, scripts, and test
patches. Repositories and venvs are created on demand.

## EvalPlus (HumanEval+ and MBPP+)

```sh
python3 import_evalplus.py --per-set 30 --seed 42
python3 import_evalplus.py --per-set 999      # every problem
python3 run.py --tasks 'humaneval-*,mbpp-*'
```

The importer downloads the test splits of
[evalplus/humanevalplus](https://huggingface.co/datasets/evalplus/humanevalplus)
(164 problems) and
[evalplus/mbppplus](https://huggingface.co/datasets/evalplus/mbppplus)
(378 problems) with standard-library HTTP. EvalPlus keeps the original problem
statements and stubs and adds tests that catch solutions overfitted to the
original examples. Each task gives the agent `solution.py` (the HumanEval
signature and docstring, or the MBPP signature, with an empty body) and the
problem statement. The official test program lives in `pristine/`, outside the
workspace, and `check.sh` copies it in at grading time; the agent can change its
solution but not the tests.

The tests import numpy, so it must be installed for the `python3` that runs
grading; the importer exits with an error otherwise. Every candidate is
validated before it is kept: the untouched stub must fail the hidden tests and
the canonical solution must pass. Sampling is deterministic for a given
`--seed`, and failed candidates are skipped in favour of the next shuffled
problem, so two machines can end up with slightly different sets if a problem
depends on a package version. Run the importer on the machine that will run the
benchmark.

The committed selection contains 30 HumanEval+ and 30 MBPP+ tasks (seed 42).
`python3 validate_tasks.py 'humaneval-*,mbpp-*'` rechecks every one
without a model.

## DS-1000 (data science)

```sh
python3 import_ds1000.py --count 30 --seed 42
python3 import_ds1000.py --libraries Pandas,Numpy,Scipy,Sklearn --count 40
python3 validate_tasks.py 'ds1000-*'
```

[DS-1000](https://github.com/xlang-ai/DS-1000) (Lai et al., 2022) is 1,000
StackOverflow-style data-science problems about pandas, numpy, scipy,
matplotlib, scikit-learn, TensorFlow and PyTorch, each with a reference
solution and an executing test. Only the `Origin` variants are sampled, so the
same problem does not appear several times under rewritten perturbations. The
importer offers only libraries installed for the grading interpreter (Pandas,
Numpy and Scipy by default). Each task gives the original problem statement and
a `result = ...` stub; the test runner lives in `pristine/`, outside the
workspace, and `check.sh` copies it in at grading time.

The committed selection contains 30 validated DS-1000 tasks (seed 42), checked
the same way as the other task families: the untouched stub must fail and the
reference solution must pass. The dataset is CC BY-SA 4.0, so the imported
problem text, reference solutions and tests remain under that license (see
attribution); the task wrappers are part of this repository. Version drift can
reject problems that newer pandas/numpy releases broke — the importer skips them
and continues with the next problem.

## FinQA (financial tables)

```sh
python3 import_finqa.py --count 20 --per-task 5 --seed 42
python3 run.py --tier showcase --tasks 'finqa-*'
```

[FinQA](https://github.com/czyssrs/FinQA) (Chen et al., EMNLP 2021) asks
questions over tables extracted from real corporate filings, with a numeric
answer for each. Each imported task bundles five examples in `questions.json`
(question, table, and the surrounding filing text) and asks for `answers.json`,
an object mapping each id to its answer. Only answers the dataset grades
objectively are kept — numbers, percentages, and yes/no; free-text answers are
excluded. Grading normalises commas, currency signs, percentages and a small
numeric tolerance (`pristine/check.py`).

This is our own answer check around the public dataset, not FinQA's official
program-execution metric: the tasks test reading a financial table and computing
the answer, not producing a FinQA program. The committed selection contains 20
tasks of five questions each, validated by comparing the gold answers with the
grader. FinQA is MIT-licensed. FinQA tasks are in the opt-in showcase tier
because they produce answers rather than code.

## Attribution and license

`NOTICE.md` lists each imported task family with its license, and copies of the
license texts sit next to it (`APACHE-2.0-LICENSE`, `HUMANEVAL-LICENSE`,
`FINQA-LICENSE`, `DS1000-LICENSE`, `EXERCISM-LICENSE`, `SWE-bench-LICENSE`,
`GPL-2.0-LICENSE`). All imported sets are open-source licensed. Two are
copyleft, so their imported files keep those terms: DS-1000 (CC BY-SA 4.0) and
the pylint tasks from SWE-bench, with the result patches made against pylint
(GPL-2.0-or-later).

[SWE-bench](https://github.com/SWE-bench/SWE-bench) and SWE-bench Lite are by
Carlos E. Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei,
Ofir Press, and Karthik Narasimhan, *SWE-bench: Can Language Models Resolve
Real-World GitHub Issues?* (ICLR 2024). SWE-bench is distributed under the
[MIT license](https://github.com/SWE-bench/SWE-bench/blob/main/LICENSE).
Repository checkouts retain their own upstream licenses. The upstream MIT
notice is included in `SWE-bench-LICENSE`.

[HumanEval](https://github.com/openai/human-eval) is by Mark Chen, Jerry Tworek,
Heewoo Jun, et al., *Evaluating Large Language Models Trained on Code* (2021),
and is distributed under the MIT license.
[MBPP](https://github.com/google-research/google-research/tree/master/mbpp) is
by Jacob Austin, Augustus Odena, Maxwell Nye, et al., *Program Synthesis with
Large Language Models* (2021), and is released by Google Research as part of
that repository under the Apache-2.0 license.
[HumanEval+ and MBPP+](https://github.com/evalplus/evalplus) and their stricter
tests are by Jiawei Liu, Chunqiu Steven Xia, Yuyao Wang, and Lingming Zhang,
*Is Your Code Generated by ChatGPT Really Correct? Rigorous Evaluation of Large
Language Models for Code Generation* (NeurIPS 2023). EvalPlus is distributed
under the [Apache-2.0 license](https://github.com/evalplus/evalplus/blob/master/LICENSE).
Imported tasks retain the upstream problem text and test programs; the
repository stores only the task wrappers.

[DS-1000](https://github.com/xlang-ai/DS-1000) is by Yuhang Lai, Chengxi Li,
Yiming Wang, Tianyi Zhang, Ruiqi Zhong, Luke Zettlemoyer, Scott Wen-tau Yih,
Daniel Fried, Sida Wang, and Tao Yu, *DS-1000: A Natural and Reliable Benchmark
for Data Science Code Generation* (ICML 2023). The dataset is distributed under
the [CC BY-SA 4.0 license](https://github.com/xlang-ai/DS-1000/blob/main/LICENSE);
the imported `ds1000-*` problem text, reference solutions, and tests remain
under that license and are attributed here, while the surrounding task
wrappers are part of this repository.

[FinQA](https://github.com/czyssrs/FinQA) is by Zhiyu Chen, Wenhu Chen, Charese
Smiley, Sameena Shah, Iana Borova, Dylan Langdon, Reema Moussa, Matt Beane,
Ting-Hao Huang, Bryan Routledge, and William Yang Wang, *FinQA: A Dataset of
Numerical Reasoning over Financial Data* (EMNLP 2021). It is distributed under
the [MIT license](https://github.com/czyssrs/FinQA/blob/master/LICENSE).
