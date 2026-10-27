# Auditing the benchmark

This benchmark measures our own tool, so don't take the tables on trust. This
page covers what each run records, how to check a result, and what was excluded
and why.

## What a result file contains

Each `results/<stamp>-<pid>.json` has a `meta` block for the run and one entry
per agent-and-task run.

`meta`:

- `agent_versions`: each agent's `--version` output.
- `chanto_bin.sha256`: the exact Chanto binary that ran; newer runs also record
  `chanto_commit`.
- `upstream_model`: the model the proxy actually routed to, and `proxy` (the
  LiteLLM version).
- `tasks`: a SHA-256 for every task's definition (prompt, setup, test patch,
  grader).
- `bench_commit` and `bench_dirty`: the benchmark's own commit, and whether it
  had uncommitted changes.
- `isolation`: how the runs were isolated (`sandbox-exec`, `bwrap`, or `off`),
  also at the top of the file. Files from before it was recorded, and files
  with `off`, were measured without isolation; `run.py --report` refuses them.
- `seed`, `timeout_s`, `offline_sandbox`, `offline_profile_sha256`, the platform
  and the exact `command`.

Each run entry has pass or fail, wall time, exit code, timeout, *false "done"*
(it claimed success but the check failed), any edited test files, token usage
metered at the proxy, a `meter_label`, start and end times, `evidence`, its
`isolation` and `offtask_hits`: what its transcript shows it reaching for outside
its task (other runs' files, installed packages, package downloads, git history,
whole-disk searches, the upstream repository on GitHub). See
[docs/sandbox.md](docs/sandbox.md#detecting-off-task-access).

**Published evidence** is each run's `.patch`: the change the agent made, new
files included, captured before grading, in `results/<stamp>-<pid>/`, and the
grader's output, inline as `check_output`. The agent's full output, its own
transcript and the full grader log are recorded too but stay on the benchmark
machine: agents that searched outside their task listed unrelated private files
in them. Their SHA-256 hashes are in the result file.
The proxy's per-call meter log isn't published either, for the same reason.

Runs from before evidence was captured automatically (most of the October 2026
hard tier) were saved afterwards in `results/hard-evidence/`. The grader had
already applied the hidden tests to those workspaces by then, so those patches
leave out the files the task's `test.patch` touches; `index.json` lists them.

## Checking a result

- **A pass or fail:** check out the task's repository at the commit in
  `tasks/<task>/instance.json`, apply the run's `.patch` and run
  `tasks/<task>/check.sh`. The check restores the test files, applies SWE-bench's
  hidden test patch and runs its `FAIL_TO_PASS` and `PASS_TO_PASS` tests. Two
  differences from official SWE-bench scoring: each listed test function runs
  whole rather than per parametrized case, and it runs in a local Python virtual
  environment rather than SWE-bench's Docker images. Every task was validated
  under this grader at import (`python3 import_swebench.py --ids <list.json>`
  repeats that).
- **That nothing changed between agents:** `meta.tasks`, `chanto_bin.sha256`,
  `upstream_model` and `bench_commit` match across every shard of a run.
- **The tasks themselves:** compare `meta.tasks` with the task folders here.
- **The statistics:** `python3 run.py --report results/<files>.json` prints pass
  rates with 95% Wilson intervals. With 25 tasks and one run each, those are
  wide: a difference of a few tasks is not a result.

## Exclusions and incidents (October 2026 hard tier)

Everything excluded is listed here.

- **The first attempt was voided whole.** Agents could read newer pytest and
  pylint releases from the machine's installed packages, which contain the
  fixes, so any pass was suspect. Its result files are in `results/void/`
  (5 runs: opencode, Claude Code and Goose passed, Pi failed). The sandbox now
  hides installed packages, package caches and the benchmark data, and every
  voided pair was rerun from scratch.
- **A crashed setup:** one shard stopped when `ensurepip` failed building a task
  environment. Setup now retries once; the pairs that never ran were run later
  with the same settings.
- **A pause:** the run was stopped to free the machine and resumed later. Runs
  in progress then left no result and were rerun. `resume_hard.py` reruns only
  pairs with no result, so no pair ran twice with the better result kept.
- **A full disk** (October 14, 13:42): one shard stopped while writing results.
  The run it had just finished (Goose on pytest-5495) was never recorded, so it
  counts as not run and was rerun.
- **A shared machine:** two shards ran in parallel. That affects wall times, not
  pass rates; don't compare speeds from this run.

## Known limitations

- **Versions.** Agents are pinned for a whole run. On the October 2026 hard tier,
  OpenCode 2.0.22 (2.0.27 was out) and Pi 1.1.0 (1.2.0 was out) weren't the
  newest; the rest were current. Each RESULTS.md section lists its versions.
- **Which tasks.** A fixed-seed sample (`import_swebench.py --seed 42`) from
  SWE-bench Lite, not Verified, limited to four repositories that set up without
  Docker (pytest, requests, Flask, pylint). `hard-tasks.txt` is the list.
- **Sample size.** 25 tasks, one run each, on a non-deterministic model.
- **One model for all.** Every agent uses the same model through LiteLLM. That
  separates the agent from the model, but agents built for one model family
  (Claude Code, Codex) run outside their home setup.
- **Isolation.** Each run has its own root and HOME and runs under
  `sandbox-exec` on macOS or bubblewrap on Linux; their rules differ in detail,
  and what neither can stop is listed in [docs/sandbox.md](docs/sandbox.md#what-it-doesnt-stop).
  The October 2026 hard tier predates this: it ran on macOS with the older
  `--offline` sandbox, which shared work folders and config homes between runs
  and only hid a list of known places, so its table is labelled as measured
  without isolation.
- **The author's own tool.** Chanto was developed alongside this benchmark, and
  its prompts were tuned on earlier tiers, not on the SWE-bench hard tier.
  Independent reruns are the real test.
- **Binary hashes.** Rust builds aren't bit-for-bit reproducible across machines,
  so a rebuild won't necessarily match `chanto_bin.sha256`.
- **Older commits.** Runs from before Chanto's public release name a
  `bench_commit` from its private development history. The task hashes in
  `meta.tasks` still let you confirm what was graded.

## Rerunning

```sh
./proxy.sh deepseek/deepseek-flash      # one model for every agent
python3 run.py --api http://localhost:4000 --meter http://localhost:4100 \
  --model bench-model --timeout 1200 --seed 121 \
  --agents chanto,claude,codex,opencode --tasks "$(paste -sd, hard-tasks.txt)"
```
