# Chanto benchmarks — agent notes

## Commands
- Runner tests: `python3 -m unittest -v test_run` (add `BENCH_SANDBOX_SMOKE=1` for the real sandbox check: sandbox-exec on macOS, bubblewrap on Linux)
- A run: `python3 run.py --agents chanto,opencode --model <model> [--tasks a,b] [--tier hard]`; `--estimate` projects cost and runs nothing
- Report from raw results: `python3 run.py --report results/<files>.json`
- The Chanto binary comes from a sibling checkout (`../chanto/target/release/chanto`); `CHANTO_REPO` or `BENCH_CHANTO_BIN` point elsewhere
- Enable the hooks once per clone: `git config core.hooksPath .githooks`; don't bypass them with `--no-verify`

## Conventions
- `results/` is the record behind published numbers: never edit or delete a result file. A run that has to be excluded moves to `results/void/` and AUDIT.md says why.
- A task's hidden tests (`tasks/<name>/pristine/`, `hidden/`) must stay unreadable to agents. The sandbox hides this repository and the Chanto sources; keep `offline_hidden` and the checkout-name rules in `run.py` covering any new place task data can live.
- Every published number names the exact versions behind it. Runs record them in `meta.agent_versions` (add new agents to `VERSION_CMDS`); each RESULTS.md section has a `Versions:` line listing every agent and the model, taken from the cited result files. Runs made outside `run.py` (like `cputurn.py`) save a raw file under `results/` with the versions, command, machine and date in its header. If a version wasn't recorded, say so; never fill it in from memory. chanto.sh shows agent names only and links here for versions.
- Changing a task changes its digest in later results' `meta.tasks`, so add a task rather than editing a published one.
- Imported tasks keep their upstream license: record the source and license in NOTICE.md and add the license text next to it.
- Commit messages follow Conventional Commits, checked by `.githooks/commit-msg` and in CI: `<type>(<scope>): <summary>`, as in [Chanto's CONTRIBUTING.md](https://github.com/chanto-sh/chanto/blob/main/CONTRIBUTING.md#commit-messages). No AI attribution lines.
