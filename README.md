# Chanto benchmarks

Benchmarks for [Chanto](https://github.com/chanto-sh/chanto): coding tasks with
automated checks, a runner that drives Chanto and other coding agents on the
same model, and every raw result behind the published numbers.

- [RESULTS.md](RESULTS.md): results, with the versions and files behind each table
- [AUDIT.md](AUDIT.md): what a run records and how to check a result yourself

## Overhead: latest results

Measured October 25, 2026 by the [reproduce workflow, run 40164648883](https://github.com/chanto-sh/benchmarks/actions/runs/40164648883)
on GitHub's own runners, from commit `be7952e` ([#3](https://github.com/chanto-sh/benchmarks/pull/3)): `python3 reproduce.py`, 16
coding agents with at least 5,000 GitHub stars, each run 10 times; the table
shows medians. Each number is in the summary of that run, under its OS.

- **macOS**: `macos-latest`, Apple M1 (Virtual), 3 cores, 7 GB RAM, macOS (Darwin 25.6.0), arm64
- **Linux**: `ubuntu-latest`, AMD EPYC 9V45, 4 cores, 16 GB RAM, Linux 6.17 (Azure), x86_64

Versions: Chanto 0.1.4; Aider 0.86.2; Claude Code 2.1.302; Cline 3.0.70; Codewhale 0.10.1; Codex 0.162.1; Continue CLI 1.5.47; Crush 0.98.1; Forge 2.13.21; Gemini CLI 0.65.0; Goose 1.54.0; Kilo Code 7.8.8; OpenHands CLI 1.16.0; opencode 2.0.22; Pi 1.1.0; Qwen Code 0.25.1. The model is a local mock (`stressmock.py`), not a real one.

| agent | runtime | CPU ms/turn, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/40164648883#summary-121083103946) | CPU ms/turn, [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/40164648883#summary-121083103832) | peak MB, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/40164648883#summary-121083103946) | peak MB, [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/40164648883#summary-121083103832) | install MB, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/40164648883#summary-121083103946) / [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/40164648883#summary-121083103832) |
|---|---|--:|--:|--:|--:|--:|
| **Chanto** | Rust | **4.9** | **3.3** | **23** | **23** | 25 / 30 |
| Goose | Rust | 15.3 | 11.2 | 168 | 145 | 269 / 308 |
| Forge | Rust | 15.9 | 11.8 | 86 | 83 | 111 / 131 |
| Crush | Go | 24.6 | 13.2 | 181 | 179 | 130 / 132 |
| Pi | Node | 18.4 | 14.2 | 178 | 176 | 158 / 164 |
| Codewhale | Rust | 38.6 | 21.0 | 124 | 175 | 86 / 105 |
| Claude Code | Node | 52.8 | 43.0 | 364 | 346 | 268 / 566 |
| Codex | Rust | 61.7 | 43.3 | 202 | 345 | 344 / 453 |
| Qwen Code | Node | 73.0 | 52.1 | 245 | 243 | 151 / 172 |
| Gemini CLI | Node | 79.9 | 52.5 | 529 | 511 | 105 / 105 |
| Continue CLI | Node | 85.8 | 55.4 | 335 | 310 | 83 / 84 |
| Cline | Node | 109.7 | 76.9 | 622 | 577 | 363 / 406 |
| Aider | Python | 111.0 | 80.6 | 256 | 244 | 688 / 607 |
| opencode | Bun | 104.9 | 98.6 | 526 | 491 | 180 / 204 |
| OpenHands | Python | 252.7 | 202.3 | 345 | 314 | 630 / 620 |
| Kilo Code | Node | 283.8 | 215.7 | 941 | 892 | 341 / 1,246 |

An instant mock model answers every request with a tool call that reads the
next 40 KB file, for 40 turns, so the context keeps growing. CPU is user + sys
time of the agent's whole process tree divided by the number of model
requests; peak memory is the largest resident set of that tree, sampled every
60 ms; install MB is what the pinned install puts on disk (Node and Python,
where needed, aren't counted). Sorted by Linux CPU. Raw files, with every run's
numbers: [`results/overhead-20261025-052453.txt`](results/overhead-20261025-052453.txt)
(macOS) and [`results/overhead-20261025-052036.txt`](results/overhead-20261025-052036.txt)
(Linux).

Notes on what isn't like for like are in [RESULTS.md](RESULTS.md#per-turn-overhead-16-agents-mock-model-october-25).

## Reproduce the overhead numbers

Copy and paste, on macOS or Linux:

```sh
git clone https://github.com/chanto-sh/benchmarks.git
cd benchmarks
python3 reproduce.py --quick   # Chanto, Goose, Codewhale, opencode: about 5 minutes
```

and for every agent in the table:

```sh
python3 reproduce.py           # all 24 agents: 20–40 minutes
```

| | `--quick` | full |
|---|---|---|
| Agents | the 4 standalone binaries | all 24: the 16 in the table, plus jcode, DeepSeek-Reasonix, oh-my-pi, Open Interpreter, Grok Build, fx, mini-swe-agent and Mistral Vibe |
| Needs | Python 3.9+, curl, tar (and unzip on macOS) | the same, plus Node 22+ with npm, and [uv](https://docs.astral.sh/uv/) |
| Runtime | about 5 minutes | 20–40 minutes (9 on GitHub's Linux runner and 13 on its macOS one before the six were added) |
| Disk | about 700 MB | up to 6 GB |

No API key and no model are needed: a local mock answers every request at
once, asking the agent to read the next 40 KB file, for 40 turns. So the CPU
time measured is the agent's own work, read from the kernel (user + sys of the
agent and everything it starts), and memory is the peak resident set of its
whole process tree. Each agent runs 10 times; the table shows medians and each
agent's ratio to Chanto. Absolute numbers depend on the machine, so compare
the ratios. Every install is pinned and checksum-verified
(`install-agents.sh`), Chanto included, as its release binary. The agents
install under `~/.local/share/chanto-bench` (set `BENCH_HOME` to put them
elsewhere; delete that folder afterwards to get the space back), and the
Python agents as uv tools.

The table is saved to `results/overhead-<date>.txt`, with the versions,
machine, settings and every run's raw numbers. `--agents` measures any subset,
including hax and zerostack, which still run here but are below the table's
5,000-star bar; `--reps` changes the number of runs.

### Run it on GitHub's machines, from a fork

To get numbers from hardware nobody here controls, without installing
anything:

1. Fork this repository (**Fork** at the top of its GitHub page).
2. In the fork, open the **Actions** tab and enable workflows (forks start
   with them off).
3. Choose **reproduce** in the list on the left, then **Run workflow**. Leave
   **quick** unticked for every agent, or tick it for the native binaries only.
4. When it finishes (a few minutes for quick, about 15 for the full run),
   open the run: its summary has the table for macOS and for Linux, and the
   results files are under **Artifacts**.

It runs the same `reproduce.py` on GitHub's `macos-latest` and `ubuntu-latest`
runners, the same way the published numbers were made.

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
the expected tokens, cost and time without running anything.

Every run is isolated, so it sees only its own task
([docs/sandbox.md](docs/sandbox.md)). Each agent, task and repetition gets its
own temporary root with a fresh `HOME` and `TMPDIR`, a checkout with no git
history past the task's base commit, and a prebuilt virtualenv with package
indexes switched off. The agent runs in an OS sandbox, `sandbox-exec` on macOS
or bubblewrap on Linux, that can read only that root, its own install and
system and toolchain paths, and can connect only to the model proxy on
localhost. So no run can read another agent's workspace, a newer release with
the fix, the upstream repository or this repository's hidden tests. After each
run the transcript is checked for attempts anyway, recorded as `offtask_hits`.

The model proxy itself is the one way out: some agents search the web *through
the model API* (Claude Code's WebSearch sends a server-side `web_search` tool,
Gemini CLI's google_web_search a `googleSearch` tool), and the upstream runs
the search outside the sandbox. Runs before this change did, and some found
published SWE-bench patches for the task being solved; their transcripts show
it as a `web search` off-task hit. The proxy now refuses a request that asks
only for a search and strips search tools and `web_search_options` from any
other ([no_search.py](no_search.py)), and the two agents run with those tools
switched off as well.
`CHANTO_BENCH_ISOLATION=off` turns the sandbox off for debugging; result files
record the mode, and `--report` refuses runs made without it.

`python3 -m unittest -v test_run` tests the runner itself;
`BENCH_SANDBOX_SMOKE=1` adds a run of a fake agent under the real sandbox.

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
