# Auditing the benchmark

This is a benchmark of our own tool, so don't take the tables on trust. This page
covers what each run records, how to check a result yourself, and which runs were
excluded and why.

## What a result file contains

Each `results/<stamp>-<pid>.json` has:

- **`meta`**, written once per run:
  - `bench_commit` and `bench_dirty`: the runner, tasks and grader as of that commit, and whether the benchmark repository had uncommitted changes.
  - `chanto_bin.sha256`: the exact Chanto binary that ran.
  - `agent_versions`: each agent's `--version` output.
  - `upstream_model`: the model the proxy really routed to, as the proxy reports it, and `proxy` (the LiteLLM version).
  - `tasks`: a SHA-256 for every task's definition (prompt, setup, test patch and grader).
  - `seed`, `timeout_s`, `offline_sandbox` and `offline_profile_sha256` (the macOS sandbox rules).
  - The platform, and the exact `command`.
- **`results`**, one entry per agent-and-task run:
  - pass/fail, wall time, exit code, timeout, "false done" (it claimed success but the check failed), and tampered test files;
  - `usage`: tokens and calls, metered at the proxy from the provider's own counts;
  - `meter_label`, which matches every model call that run made in the meter log;
  - start and end times;
  - `evidence`: three files kept next to the result in `results/<stamp>-<pid>/`, each with its SHA-256:
    - `<agent>~<task>~<rep>.out`: the agent's full output;
    - `.patch`: the change it made, new files included, taken before the grader ran;
    - `.check.txt`: everything the grader printed.
    - `.session<N>.json` / `.jsonl`: the agent's own step-by-step transcript, where it keeps one (Chanto, Claude Code, Codex and others that write JSON lines into their config home), for runs from October 14 evening on.

The October 2026 hard tier's result files and evidence are committed once the run finishes; until then they exist only on the machine running it. Runs from before evidence was recorded automatically (most of the October 2026 hard tier) were saved afterwards in `results/hard-evidence/`. By then the grader had already applied the hidden tests to those workspaces, so their patches leave out the files that the task's `test.patch` touches. `index.json` lists those files for each run.

## Checking a result yourself

- **A pass or fail:** take the task's repository at the commit in `tasks/<task>/instance.json`, apply the run's `.patch`, then run `tasks/<task>/check.sh`. The check restores the test files to their original state, applies SWE-bench's hidden test patch, and runs SWE-bench's FAIL_TO_PASS and PASS_TO_PASS tests. It differs from official SWE-bench scoring in two ways:
  - it runs each listed test function whole, not each parametrized case;
  - it runs in a local Python 3.9 virtual environment, not SWE-bench's Docker images.

  Every task was checked under this grader when it was imported: the original code fails and SWE-bench's reference fix passes. To repeat that check: `python3 import_swebench.py --ids <list.json>`.
- **That an agent did the work itself:** read its `.out`. In offline mode it couldn't reach the internet, the fixed upstream release in other installed packages, the other agents' workspaces or earlier results.
- **That tokens weren't misreported:** filter the meter log (`logs/meter-*.jsonl`) by the run's `meter_label`.
- **That nothing changed between agents:** `meta.tasks`, `chanto_bin.sha256`, `upstream_model` and `bench_commit` are the same in every shard's file.
- **The statistics:** `python3 run.py --report results/<files>.json` prints pass rates with 95% Wilson confidence intervals. With 25 tasks and one run each, those intervals are wide. A difference of a few tasks is not a result.

## Exclusions and incidents (October 2026 hard tier)

Nothing is dropped silently. Everything excluded is listed here.

- **The first attempt was voided whole, regardless of outcome.** Agents could read newer releases of pytest and pylint from the machine's installed packages, which already contain the fixes. That makes any pass suspect, whoever got it. The attempt's complete result files are in `results/void/`: 5 runs, of which opencode, claude and goose passed and pi failed. The sandbox was fixed to hide all installed packages, package caches and the bench data, and every voided pair was rerun from scratch. Those transcripts weren't kept.
- **A crashed setup:** one shard stopped when Python's `ensurepip` failed while building a task environment. Setup now retries once. The pairs that never ran were run later with the same settings.
- **A pause on request:** the run was stopped to free the machine and resumed later. The runs in progress at that moment (one per shard) left no result and were rerun from scratch. `resume_hard.py` reruns only pairs with no result line, so no pair is ever run twice and the better result kept.
- **Disk full:** the machine's disk filled up during the resumed run (October 14, 13:42). One shard stopped while writing its results. The run it had just finished (goose on pytest-5495) was printed in the log but never recorded, so it counts as not run and was rerun. `resume_hard.py` and `archive_evidence.py` take what's done from the result files, not the logs, so a lost write can't be counted.
- **Shared machine:** two shards ran in parallel, and there were a few light, non-build activities on the same machine. That affects wall times, not pass rates. Don't compare speeds from this run.

## Known limitations

- **Agent versions.** Agents are pinned for the whole of a run so that every one of its results comes from one version. On the October 2026 hard tier, two weren't the newest release when the run started: OpenCode V2 2.0.22 (2.0.27 was out) and pi 1.1.0 (1.2.0 was out). The others were current: Claude Code 2.1.300, codex-cli 0.162.1, goose 1.54.0, Qwen Code 0.25.1, Kilo 7.8.8, Crush 0.98.1 and Aider 0.86.2. Repeat runs upgrade all of them first.

- **Which tasks.** The 25 tasks are a fixed-seed sample (`import_swebench.py --seed 42`) from SWE-bench Lite. That's not Verified. The sample is limited to four repositories that can be set up without Docker: pytest, requests, flask and pylint. Tasks whose reference fix didn't pass under this grader were dropped at import. `hard-tasks.txt` is the list.

- **Sample size.** 25 tasks, one run each, on a non-deterministic model. Repeat runs and paired per-task comparisons are needed before claiming one agent beats another.
- **One model for all.** Every agent talks to the same model (`upstream_model`) through LiteLLM. That isolates the agent from the model, but agents built for a particular model family (Claude Code for Claude, Codex for GPT) run outside their home setup, and the format translation may hurt some more than others.
- **Offline sandbox.** `--offline` uses `sandbox-exec` on macOS and bubblewrap with socat on Linux. The Linux version blocks the network except the proxy ports and hides the same paths, but its rules differ in detail from macOS. The October 2026 hard tier ran on macOS. Runs without `--offline` can't rule out the contamination described above.
- **The author's own tool.** Chanto was developed alongside this benchmark and its prompts were tuned on earlier tiers. The SWE-bench hard tier was not used for tuning. Independent reruns are the real test, and all the scripts, tasks, raw results and evidence are here for that.
- **Binary hashes.** Rust builds are not bit-for-bit reproducible across machines, so a rebuild won't necessarily match `chanto_bin.sha256`. Prebuilt release binaries make this checkable.
- **Commits in older result files.** Runs recorded before Chanto's public release name a `bench_commit` from its private development history, which isn't published. What those runs graded is still checkable: `meta.tasks` holds each task's SHA-256 digest, which you can compare with the task folders here. Newer runs also record `chanto_commit`, the Chanto sources the binary was built from.

## Rerunning

```sh
./proxy.sh deepseek/deepseek-flash      # one model for every agent
python3 run.py --api http://localhost:4000 --meter http://localhost:4100 \
  --model bench-model --offline --timeout 1200 --seed 121 \
  --agents chanto,claude,codex,opencode --tasks "$(paste -sd, hard-tasks.txt)"
```
