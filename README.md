# Chanto benchmarks

Benchmarks for [Chanto](https://github.com/chanto-sh/chanto): coding tasks with
automated checks, a runner that drives Chanto and other coding agents on the
same model, and every raw result behind the published numbers.

- [RESULTS.md](RESULTS.md): results, with the versions and files behind each table
- [AUDIT.md](AUDIT.md): what a run records and how to check a result yourself

## Reproduce the overhead numbers

One command installs every agent at the version [RESULTS.md](RESULTS.md)
reports, measures each one against a local mock model, and prints the table:

```sh
git clone https://github.com/chanto-sh/benchmarks.git chanto-benchmarks
cd chanto-benchmarks
python3 reproduce.py --quick   # Chanto, hax, zerostack, Goose, Codewhale, opencode: a few minutes
python3 reproduce.py           # all 18 agents (needs npm and uv): about an hour
```

It needs Python 3.9+, curl and tar on macOS or Linux, and no API key: the mock
answers every request at once, asking the agent to read the next 40 KB file,
for 40 turns. So the CPU time measured is the agent's own work, read from the
kernel (user + sys of the agent and everything it starts), and memory is the
peak resident set of its whole process tree. Each agent runs 10 times; the
table shows medians and each agent's ratio to Chanto. Absolute numbers depend
on the machine, so compare the ratios. Every install is pinned and
checksum-verified (`install-agents.sh`), Chanto included, as its release
binary.

The table is also saved to `results/overhead-<date>.txt`, with the versions,
machine, settings and every run's raw numbers. To get numbers from machines
nobody here controls, fork this repository and run the **reproduce** workflow
(Actions → reproduce → Run workflow): it runs the same command on GitHub's
macOS and Linux runners and puts the table in the run's summary.

## Run it

Clone this next to a Chanto checkout and build Chanto. The runner uses
`../chanto/target/release/chanto` (set `CHANTO_REPO` or `BENCH_CHANTO_BIN` to
point elsewhere). The runner itself needs only Python 3; `install-agents.sh`
installs the agents it compares at pinned versions (with npm, uv and
checksum-verified downloads) into `~/.local/share/chanto-bench`, which runs use
before anything on your PATH.

```sh
git clone https://github.com/chanto-sh/chanto.git
git clone https://github.com/chanto-sh/benchmarks.git chanto-benchmarks
(cd chanto && cargo build --release)
cd chanto-benchmarks
./install-agents.sh      # the other agents, at the versions RESULTS.md reports

# A local model through Ollama
python3 run.py --agents chanto,opencode,claude --model qwen3.8-bench

# Or a hosted model through the proxy (start it in another terminal)
./proxy.sh deepseek/deepseek-flash
python3 run.py --api http://localhost:4000 --agents chanto,opencode,claude,codex --tier hard
```

`--tasks` picks tasks by name or glob, `--tier` by tier, and `--estimate` prints
the expected tokens, cost and time without running anything. `--offline` runs
each agent in a sandbox that hides this repository, the Chanto sources and
package caches, so agents can't read hidden tests or earlier runs
([docs/sandbox.md](docs/sandbox.md)).

`python3 -m unittest -v test_run` tests the runner itself.

## Tasks

Each task is a folder in `tasks/` with a prompt, starting files and a
`check.sh` that decides pass or fail. Tasks are grouped into tiers by name:

| Tier | Tasks | What it covers |
|---|---|---|
| core | `poly-*`, `humaneval-*`, `mbpp-*`, `trap-*` | Small exercises in several languages |
| medium | `ds1000-*` and hand-written tasks | Bug fixes, features, refactors, test writing |
| hard | `swe-*` | Real GitHub issues from SWE-bench Lite and Verified |
| beyond | `coding-*`, `math-*`, `physics-*`, `trap-imp-*` | Work that can't be faked: hidden inputs, impossible requests |
| showcase (opt-in) | `data-*`, `analysis-*`, `nontrad-*`, `finqa-*` | Answers rather than code; scored separately |

A run covers the four coding tiers unless `--tier` says otherwise.
[docs/tasks.md](docs/tasks.md) has the task format and the tiers in detail, and
[docs/importing.md](docs/importing.md) covers the public datasets (SWE-bench,
EvalPlus, DS-1000, FinQA, Aider's polyglot set).

## License

The runner, scripts and the tasks written here are under the
[Apache License 2.0](LICENSE). Imported tasks keep their upstream licenses,
including CC BY-SA 4.0 (DS-1000) and GPL-2.0-or-later (the pylint tasks);
[NOTICE.md](NOTICE.md) lists each source with its license.
