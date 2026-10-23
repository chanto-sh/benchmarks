# Offline runs and timeouts

```sh
python3 run.py --offline --agents chanto --tasks 'swe-*'
python3 -m unittest -v test_run
# Also exercise the real sandbox (no model needed):
BENCH_SANDBOX_SMOKE=1 python3 -m unittest -v test_run
```

## What `--offline` does

The agent and its child processes run in a sandbox: `sandbox-exec` on macOS,
bubblewrap with socat on Linux. Import, setup and grading run outside it.
Platforms without one are rejected before any task is set up.

**Network:** outbound connections are blocked except to localhost, for Ollama or
the local model proxy and meter. Unix sockets still work. A local proxy can still
call a hosted provider on the agent's behalf.

**Files:** agents can't read or write

- this repository (task data, hidden tests, past results) and the Chanto checkout,
- any other checkout of this repository, matched by folder name,
- `~/.cache/chanto-bench/` and `~/.local/share/chanto-bench/` (other runs' work
  folders, cached datasets), and the work root (`BENCH_WORK`),
- package caches that could hold a newer release with the fix (pip, uv, Hugging Face).

The current task's workspace and the agent's config home are the exceptions.
The Chanto binary gets a read-only exception for that one file. Everything else
on disk is unrestricted: this keeps answers away from agents, it isn't a general
security boundary.

Chanto's own sandbox is turned off for the run, since it would nest inside this
one, and its config is restored afterwards, including on a timeout or launch
error. Runs that share a work folder or config home shouldn't run at the same
time.

## Processes and timeouts

Agent, setup and grading commands each run in their own process group. After
the agent exits or times out, the runner kills what's left in its group before
grading. Children that start their own session or process group escape that
cleanup.

- Agent timeout: the result records `timed_out: true` and `exit_code: -1`.
- Grading timeout: exit code 124 with a timeout message.
- SWE tasks: 1800 seconds for the agent (`--timeout` overrides), 600 for setup
  (not counted as agent time) and 600 for grading.

Every result file records whether the run was `offline`.
