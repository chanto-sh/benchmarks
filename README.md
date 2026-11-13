# Chanto benchmarks

Benchmarks for [Chanto](https://github.com/chanto-sh/chanto): coding tasks with
automated checks, a runner that drives Chanto and other coding agents on the
same model, and every raw result behind the published numbers.

- [RESULTS.md](RESULTS.md): results, with the versions and files behind each table
- [AUDIT.md](AUDIT.md): what a run records and how to check a result yourself

## Overhead: latest results

Measured November 13, 2026 by the [reproduce workflow, run 43385862263](https://github.com/chanto-sh/benchmarks/actions/runs/43385862263)
on GitHub's own runners: `python3 reproduce.py`, the 23
coding agents with at least 5,000 GitHub stars, each run 10 times; the table
shows medians. Each number is in the summary of that run, under its OS.

- **macOS**: `macos-latest`, Apple M1 (Virtual), 3 cores, 7 GB RAM, macOS (Darwin 25.6.0), arm64
- **Linux**: `ubuntu-latest`, Intel Xeon Platinum 8370C, 4 cores, 16 GB RAM, Linux 7.0 (Azure), x86_64
- **Windows**: `windows-latest`, AMD EPYC 7763, 4 cores, 16 GB RAM, Windows Server 2025, AMD64

Versions: Chanto 0.1.20; Aider 0.86.2; Claude Code 2.1.323; Cline 3.0.74; Codewhale 0.10.2; Codex 0.168.0; Continue CLI 1.5.47; Crush 0.101.0; DeepSeek-Reasonix 2.61.0; Forge 2.13.21; Gemini CLI 0.68.0; Goose 1.59.0; Grok Build 1.0.77; jcode 0.99.1; Kilo Code 7.8.27; mini-swe-agent 2.4.6; Mistral Vibe 3.1.2; oh-my-pi 18.20.0; Open Interpreter 0.0.61; OpenHands CLI 1.16.0; opencode 2.2.7; Pi 1.5.2; Qwen Code 0.27.3. The model is a local mock (`stressmock.py`), not a real one.

| agent | runtime | startup ms, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/43385862263#summary-131754315911) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/43385862263#summary-131754315874) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/43385862263#summary-131754315863) | CPU ms/turn, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/43385862263#summary-131754315911) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/43385862263#summary-131754315874) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/43385862263#summary-131754315863) | peak MB, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/43385862263#summary-131754315911) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/43385862263#summary-131754315874) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/43385862263#summary-131754315863) | install MB, macOS / Linux / Windows |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **Chanto** | Rust | **14** | **10** | **55** | **2.1** | **2.9** | **4.7** | **18** | **23** | **18** | 21 / 25 / 30 |
| Grok Build | Rust | 442 | 718 | 797 | 12.9 | 7.2 | 23.4 | 112 | 228 | 64 | 185 / 202 / 182 |
| Pi | Node | 504 | 466 | 648 | 10.4 | 10.8 | 13.9 | 175 | 160 | 138 | 160 / 166 / 115 |
| jcode | Rust | 148 | 35 | 102 | 13.5 | 11.0 | 17.0 | 50 | 73 | 32 | 143 / 171 / 135 |
| Goose | Rust | 361 | 428 | 633 | 15.0 | 11.7 | 23.6 | 178 | 154 | 92 | 177 / 209 / 172 |
| Forge | Rust | 238 | 197 | 875 | 12.3 | 11.8 | 21.3 | 86 | 81 | 83 | 111 / 131 / 98 |
| Crush | Go | 373 | 334 | 672 | 22.5 | 16.2 | 15.2 | 178 | 179 | 143 | 138 / 140 / 140 |
| DeepSeek-Reasonix | Go | 294 | 165 | 789 | 12.3 | 20.4 | 19.7 | 72 | 80 | 67 | 49 / 53 / 58 |
| mini-swe-agent | Python | 2942 | 3374 | 5102 | 25.9 | 22.2 | 74.0 | 243 | 235 | 252 | 486 / 603 / 434 |
| oh-my-pi | Bun | 1155 | 1522 | 2422 | 19.9 | 24.9 | 25.0 | 347 | 408 | 311 | 223 / 288 / 252 |
| Gemini CLI | Node | 2015 | 2290 | 3359 | 31.9 | 28.9 | 51.6 | 531 | 512 | 415 | 105 / 106 / 112 |
| Qwen Code | Node | 1545 | 1856 | 4781 | 30.8 | 30.9 | 129.8 | 236 | 237 | 421 | 281 / 320 / 202 |
| Codewhale | Rust | 355 | 240 | 1203 | 34.8 | 36.6 | 36.7 | 138 | 236 | 179 | 90 / 110 / 135 |
| Mistral Vibe | Python | 1979 | 2622 | 4359 | 36.7 | 41.2 | 70.5 | 255 | 244 | 246 | 210 / 348 / 197 |
| Claude Code | Node | 592 | 473 | 891 | 49.8 | 45.4 | 54.5 | 343 | 298 | 286 | 353 / 363 / 368 |
| Open Interpreter | Rust | 98 | 120 | 188 | 19.6 | 50.1 | 604.9 | 98 | 304 | 150 | 251 / 299 / 340 |
| Continue CLI | Node | 1626 | 1480 | 1906 | 54.7 | 58.5 | 75.2 | 336 | 309 | 220 | 83 / 84 / 86 |
| Codex | Rust | 373 | 469 | 602 | 42.9 | 59.3 | 774.8 | 160 | 228 | 248 | 381 / 463 / 505 |
| opencode | Bun | 2498 | 2898 | 3219 | 52.1 | 63.4 | 60.7 | 567 | 542 | 526 | 248 / 259 / 266 |
| Cline | Node | 1640 | 1732 | 2797 | 42.2 | 74.6 | 70.1 | 569 | 600 | 549 | 369 / 424 / 321 |
| OpenHands | Python | 7137 | 7384 | 13805 | 93.8 | 101.5 | 328.7 | 346 | 332 | 463 | 645 / 638 / 536 |
| Kilo Code | Node | 7365 | 9261 | 10516 | 109.8 | 124.1 | 251.0 | 930 | 814 | 714 | 387 / 723 / 665 |
| Aider | Python | 3323 | 3601 | 5062 | 176.1 | 178.0 | 193.1 | 326 | 308 | 284 | 690 / 610 / 526 |

An instant mock model answers every request with a tool call that reads the
next 40 KB file, for 40 turns, so the context keeps growing. **Startup** is the
CPU of a run that makes one model request and exits. **CPU per turn** is the
rest of a full run's CPU, startup taken out, over the requests after the
first; before this run the table had one figure that mixed the two, so an
agent slow to start looked costly on every turn. CPU is user + sys time of the
agent's whole process tree; peak memory is the largest resident set of that
tree, sampled every 60 ms; install MB is what the pinned install puts on disk
(Node and Python, where needed, aren't counted). Sorted by Linux CPU per turn.
Raw files, with every run's numbers: [`results/overhead-20261113-075250.txt`](results/overhead-20261113-075250.txt)
(macOS), [`results/overhead-20261113-074916.txt`](results/overhead-20261113-074916.txt)
(Linux), and [`results/overhead-20261113-081736.txt`](results/overhead-20261113-081736.txt)
(Windows).

Notes on what isn't like for like are in [RESULTS.md](RESULTS.md#overhead-23-agents-startup-and-per-turn-mock-model-november-13).

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
