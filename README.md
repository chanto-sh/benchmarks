# Chanto benchmarks

Benchmarks for [Chanto](https://github.com/chanto-sh/chanto): coding tasks with
automated checks, a runner that drives Chanto and other coding agents on the
same model, and every raw result behind the published numbers.

- [RESULTS.md](RESULTS.md): results, with the versions and files behind each table
- [AUDIT.md](AUDIT.md): what a run records and how to check a result yourself

## Overhead: latest results

Measured November 23, 2026 by the [reproduce workflow, run 45236642913](https://github.com/chanto-sh/benchmarks/actions/runs/45236642913)
on GitHub's own runners: `python3 reproduce.py`, the 23
coding agents with at least 5,000 GitHub stars, each run 10 times; the table
shows medians. Each number is in the summary of that run, under its OS.

- **macOS**: `macos-latest`, Apple M1 (Virtual), 3 cores, 7 GB RAM, macOS (Darwin 25.6.0), arm64
- **Linux**: `ubuntu-latest`, AMD EPYC 9V74, 4 cores, 16 GB RAM, Linux 7.0 (Azure), x86_64
- **Windows**: `windows-latest`, AMD EPYC 9V45, 4 cores, 16 GB RAM, Windows Server 2025, AMD64

Versions: Chanto 0.1.25; Aider 0.86.2; Claude Code 2.1.330; Cline 3.0.75; Codewhale 0.10.3; Codex 0.171.0; Continue CLI 1.5.47; Crush 0.102.0; DeepSeek-Reasonix 2.61.0; Forge 2.13.21; Gemini CLI 0.70.0; Goose 1.60.2; Grok Build 1.0.92; jcode 1.0.3; Kilo Code 7.8.32; mini-swe-agent 2.4.6; Mistral Vibe 3.1.4; oh-my-pi 19.1.1; Open Interpreter 0.0.61; OpenHands CLI 1.16.0; opencode 2.4.1; Pi 1.6.0; Qwen Code 0.28.4. The model is a local mock (`stressmock.py`), not a real one.

| agent | runtime | startup ms, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/45236642913#summary-137910394664) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/45236642913#summary-137910394633) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/45236642913#summary-137910394634) | CPU ms/turn, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/45236642913#summary-137910394664) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/45236642913#summary-137910394633) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/45236642913#summary-137910394634) | peak MB, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/45236642913#summary-137910394664) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/45236642913#summary-137910394633) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/45236642913#summary-137910394634) | install MB, macOS / Linux / Windows |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **Chanto** | Rust | **11** | **10** | **31** | **1.2** | **2.3** | **2.0** | **18** | **23** | **17** | 21 / 25 / 30 |
| jcode | Rust | 122 | 32 | 78 | 7.6 | 4.7 | 8.6 | 46 | 74 | 28 | 162 / 154 / 154 |
| Grok Build | Rust | 316 | 663 | 430 | 8.1 | 5.0 | 12.7 | 112 | 243 | 63 | 191 / 208 / 187 |
| Goose | Rust | 257 | 254 | 477 | 7.4 | 8.5 | 13.5 | 189 | 129 | 101 | 182 / 213 / 176 |
| Pi | Node | 295 | 387 | 406 | 6.6 | 8.9 | 7.4 | 181 | 159 | 142 | 169 / 176 / 123 |
| Codewhale | Rust | 322 | 145 | 922 | 11.5 | 9.5 | 15.0 | 160 | 303 | 145 | 124 / 151 / 192 |
| Forge | Rust | 144 | 195 | 500 | 7.8 | 10.8 | 12.3 | 89 | 80 | 87 | 111 / 131 / 98 |
| DeepSeek-Reasonix | Go | 188 | 167 | 414 | 9.4 | 14.6 | 12.3 | 71 | 81 | 66 | 49 / 53 / 58 |
| Crush | Go | 234 | 284 | 422 | 15.5 | 15.0 | 10.0 | 177 | 179 | 145 | 139 / 141 / 141 |
| oh-my-pi | Bun | 745 | 1202 | 1711 | 11.3 | 17.2 | 15.8 | 346 | 412 | 321 | 233 / 301 / 261 |
| mini-swe-agent | Python | 2430 | 3178 | 3953 | 23.2 | 19.9 | 51.3 | 247 | 241 | 254 | 498 / 610 / 448 |
| Gemini CLI | Node | 1445 | 1999 | 2211 | 18.4 | 23.8 | 22.7 | 502 | 470 | 387 | 105 / 105 / 112 |
| Qwen Code | Node | 1129 | 1656 | 2680 | 23.0 | 28.0 | 81.7 | 231 | 227 | 421 | 285 / 324 / 206 |
| Mistral Vibe | Python | 2343 | 3042 | 3344 | 29.3 | 32.3 | 41.6 | 304 | 303 | 298 | 281 / 439 / 267 |
| Claude Code | Node | 342 | 433 | 617 | 33.8 | 45.5 | 40.0 | 365 | 319 | 317 | 364 / 381 / 388 |
| Open Interpreter | Rust | 78 | 109 | 133 | 14.6 | 45.5 | 372.1 | 98 | 304 | 151 | 251 / 299 / 340 |
| Continue CLI | Node | 942 | 1297 | 1227 | 42.2 | 51.6 | 46.5 | 336 | 308 | 221 | 83 / 84 / 86 |
| opencode | Bun | 1637 | 2911 | 2617 | 34.0 | 53.9 | 42.6 | 574 | 537 | 513 | 240 / 275 / 278 |
| Codex | Rust | 198 | 419 | 328 | 27.4 | 54.4 | 507.0 | 150 | 220 | 248 | 395 / 444 / 540 |
| Cline | Node | 1118 | 1547 | 2195 | 40.0 | 78.7 | 50.2 | 707 | 669 | 648 | 381 / 435 / 333 |
| OpenHands | Python | 6307 | 6788 | 9359 | 76.4 | 80.1 | 218.0 | 356 | 348 | 473 | 485 / 524 / 424 |
| Kilo Code | Node | 5677 | 7958 | 7008 | 81.9 | 108.0 | 153.1 | 940 | 865 | 780 | 379 / 1,402 / 677 |
| Aider | Python | 3059 | 3068 | 3094 | 144.9 | 145.9 | 111.8 | 329 | 316 | 287 | 694 / 610 / 526 |

An instant mock model answers every request with a tool call that reads the
next 40 KB file, for 40 turns, so the context keeps growing. **Startup** is the
CPU of a run that makes one model request and exits. **CPU per turn** is the
rest of a full run's CPU, startup taken out, over the requests after the
first; before this run the table had one figure that mixed the two, so an
agent slow to start looked costly on every turn. CPU is user + sys time of the
agent's whole process tree; peak memory is the largest resident set of that
tree, sampled every 60 ms; install MB is what the pinned install puts on disk
(Node and Python, where needed, aren't counted). Sorted by Linux CPU per turn.
Raw files, with every run's numbers: [`results/overhead-20261123-183658.txt`](results/overhead-20261123-183658.txt)
(macOS), [`results/overhead-20261123-183654.txt`](results/overhead-20261123-183654.txt)
(Linux), and [`results/overhead-20261123-185702.txt`](results/overhead-20261123-185702.txt)
(Windows).

Notes on what isn't like for like are in [RESULTS.md](RESULTS.md#overhead-23-agents-startup-and-per-turn-mock-model-november-23).

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
