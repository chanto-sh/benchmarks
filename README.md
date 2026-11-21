# Chanto benchmarks

Benchmarks for [Chanto](https://github.com/chanto-sh/chanto): coding tasks with
automated checks, a runner that drives Chanto and other coding agents on the
same model, and every raw result behind the published numbers.

- [RESULTS.md](RESULTS.md): results, with the versions and files behind each table
- [AUDIT.md](AUDIT.md): what a run records and how to check a result yourself

## Overhead: latest results

Measured November 21, 2026 by the [reproduce workflow, run 44850066106](https://github.com/chanto-sh/benchmarks/actions/runs/44850066106)
on GitHub's own runners: `python3 reproduce.py`, the 23
coding agents with at least 5,000 GitHub stars, each run 10 times; the table
shows medians. Each number is in the summary of that run, under its OS.

- **macOS**: `macos-latest`, Apple M1 (Virtual), 3 cores, 7 GB RAM, macOS (Darwin 25.6.0), arm64
- **Linux**: `ubuntu-latest`, AMD EPYC 9V74, 4 cores, 16 GB RAM, Linux 7.0 (Azure), x86_64
- **Windows**: `windows-latest`, not measured in this run

Versions: Chanto 0.1.22; Aider 0.86.2; Claude Code 2.1.330; Cline 3.0.74; Codewhale 0.10.2; Codex 0.171.0; Continue CLI 1.5.47; Crush 0.102.0; DeepSeek-Reasonix 2.61.0; Forge 2.13.21; Gemini CLI 0.70.0; Goose 1.60.2; Grok Build 1.0.92; jcode 1.0.1; Kilo Code 7.8.32; mini-swe-agent 2.4.6; Mistral Vibe 3.1.4; oh-my-pi 19.0.1; Open Interpreter 0.0.61; OpenHands CLI 1.16.0; opencode 2.3.2; Pi 1.6.0; Qwen Code 0.28.0. The model is a local mock (`stressmock.py`), not a real one.

| agent | runtime | startup ms, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/44850066106#summary-136679302178) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/44850066106#summary-136679302168) | Windows | CPU ms/turn, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/44850066106#summary-136679302178) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/44850066106#summary-136679302168) | Windows | peak MB, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/44850066106#summary-136679302178) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/44850066106#summary-136679302168) | Windows | install MB, macOS / Linux / Windows |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Crush | Go | 197 | 172 | — | 0.0 | -0.0 | — | 271 | 270 | — | 139 / 141 / — |
| **Chanto** | Rust | **17** | **12** | — | **2.0** | **2.8** | — | **18** | **23** | — | 21 / 25 / — |
| jcode | Rust | 118 | 38 | — | 7.5 | 5.8 | — | 48 | 71 | — | 161 / 191 / — |
| Grok Build | Rust | 305 | 836 | — | 7.5 | 7.4 | — | 112 | 248 | — | 191 / 208 / — |
| Goose | Rust | 391 | 512 | — | 14.5 | 10.0 | — | 189 | 171 | — | 182 / 213 / — |
| Pi | Node | 525 | 466 | — | 10.7 | 10.2 | — | 180 | 157 | — | 169 / 175 / — |
| Forge | Rust | 240 | 247 | — | 12.9 | 12.6 | — | 87 | 81 | — | 111 / 131 / — |
| DeepSeek-Reasonix | Go | 196 | 168 | — | 9.6 | 21.5 | — | 70 | 80 | — | 49 / 53 / — |
| mini-swe-agent | Python | 2243 | 3480 | — | 21.0 | 22.4 | — | 244 | 238 | — | 497 / 610 / — |
| oh-my-pi | Bun | 767 | 1736 | — | 10.8 | 24.1 | — | 358 | 420 | — | 229 / 296 / — |
| Gemini CLI | Node | 2532 | 2327 | — | 36.4 | 27.3 | — | 503 | 471 | — | 105 / 105 / — |
| Qwen Code | Node | 1862 | 1810 | — | 47.0 | 30.5 | — | 232 | 228 | — | 281 / 320 / — |
| Codewhale | Rust | 379 | 230 | — | 36.1 | 31.4 | — | 140 | 229 | — | 90 / 110 / — |
| Mistral Vibe | Python | 3025 | 3511 | — | 52.6 | 38.3 | — | 311 | 304 | — | 281 / 439 / — |
| Claude Code | Node | 652 | 463 | — | 68.7 | 44.9 | — | 350 | 319 | — | 364 / 381 / — |
| Continue CLI | Node | 1750 | 1464 | — | 82.4 | 55.8 | — | 336 | 308 | — | 83 / 84 / — |
| Open Interpreter | Rust | 74 | 134 | — | 13.4 | 56.4 | — | 98 | 280 | — | 251 / 299 / — |
| opencode | Bun | 2878 | 3003 | — | 60.4 | 58.6 | — | 607 | 561 | — | 226 / 253 / — |
| Codex | Rust | 440 | 489 | — | 60.4 | 61.4 | — | 157 | 227 | — | 395 / 444 / — |
| Cline | Node | 2103 | 1613 | — | 59.3 | 69.0 | — | 578 | 603 | — | 369 / 424 / — |
| OpenHands | Python | 6955 | 7881 | — | 94.1 | 97.1 | — | 355 | 345 | — | 485 / 523 / — |
| Kilo Code | Node | 8744 | 8553 | — | 168.7 | 117.1 | — | 909 | 832 | — | 379 / 1,402 / — |
| Aider | Python | 3716 | 3440 | — | 181.3 | 182.8 | — | 328 | 316 | — | 690 / 610 / — |

An instant mock model answers every request with a tool call that reads the
next 40 KB file, for 40 turns, so the context keeps growing. **Startup** is the
CPU of a run that makes one model request and exits. **CPU per turn** is the
rest of a full run's CPU, startup taken out, over the requests after the
first; before this run the table had one figure that mixed the two, so an
agent slow to start looked costly on every turn. CPU is user + sys time of the
agent's whole process tree; peak memory is the largest resident set of that
tree, sampled every 60 ms; install MB is what the pinned install puts on disk
(Node and Python, where needed, aren't counted). Sorted by Linux CPU per turn.
Raw files, with every run's numbers: [`results/overhead-20261121-031156.txt`](results/overhead-20261121-031156.txt)
(macOS), and [`results/overhead-20261121-030739.txt`](results/overhead-20261121-030739.txt)
(Linux).

Notes on what isn't like for like are in [RESULTS.md](RESULTS.md#overhead-23-agents-startup-and-per-turn-mock-model-november-21).

## Reproduce the overhead numbers

Copy and paste, on macOS or Linux:

```sh
git clone https://github.com/chanto-sh/benchmarks.git
cd benchmarks
python3 reproduce.py --quick   # Chanto, Goose, Codewhale, opencode: about 5 minutes
```

and for every agent in the table:

```sh
python3 reproduce.py           # all 23 agents: 20–40 minutes
```

| | `--quick` | full |
|---|---|---|
| Agents | the 4 standalone binaries | the 23 in the table (fx, hax and zerostack, below 5,000 stars, run when `--agents` names them) |
| Needs | Python 3.9+, curl, tar (and unzip on macOS) | the same, plus Node 22+ with npm, and [uv](https://docs.astral.sh/uv/) |
| Runtime | about 5 minutes | 20–40 minutes (about 20 on GitHub's Linux and macOS runners, about 45 on Windows) |
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
4. When it finishes (a few minutes for quick, about 20 for the full run),
   open the run: its summary has the table for macOS, Linux and Windows, and the
   results files are under **Artifacts**.

It runs the same `reproduce.py` on GitHub's `macos-latest`, `ubuntu-latest` and
`windows-latest` runners, the same way the published numbers were made.

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
