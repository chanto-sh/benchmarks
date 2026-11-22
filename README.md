# Chanto benchmarks

Benchmarks for [Chanto](https://github.com/chanto-sh/chanto): coding tasks with
automated checks, a runner that drives Chanto and other coding agents on the
same model, and every raw result behind the published numbers.

- [RESULTS.md](RESULTS.md): results, with the versions and files behind each table
- [AUDIT.md](AUDIT.md): what a run records and how to check a result yourself

## Overhead: latest results

Measured November 22, 2026 by the [reproduce workflow, run 44962994960](https://github.com/chanto-sh/benchmarks/actions/runs/44962994960)
on GitHub's own runners: `python3 reproduce.py`, the 23
coding agents with at least 5,000 GitHub stars, each run 10 times; the table
shows medians. Each number is in the summary of that run, under its OS.

- **macOS**: `macos-latest`, Apple M1 (Virtual), 3 cores, 7 GB RAM, macOS (Darwin 25.6.0), arm64
- **Linux**: `ubuntu-latest`, AMD EPYC 9V74, 4 cores, 16 GB RAM, Linux 7.0 (Azure), x86_64
- **Windows**: `windows-latest`, AMD EPYC 7763, 4 cores, 16 GB RAM, Windows Server 2025, AMD64

Versions: Chanto 0.1.23; Aider 0.86.2; Claude Code 2.1.330; Cline 3.0.75; Codewhale 0.10.2; Codex 0.171.0; Continue CLI 1.5.47; Crush 0.102.0; DeepSeek-Reasonix 2.61.0; Forge 2.13.21; Gemini CLI 0.70.0; Goose 1.60.2; Grok Build 1.0.92; jcode 1.0.1; Kilo Code 7.8.32; mini-swe-agent 2.4.6; Mistral Vibe 3.1.4; oh-my-pi 19.1.0; Open Interpreter 0.0.61; OpenHands CLI 1.16.0; opencode 2.3.2; Pi 1.6.0; Qwen Code 0.28.3. The model is a local mock (`stressmock.py`), not a real one.

| agent | runtime | startup ms, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/44962994960#summary-137025897192) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/44962994960#summary-137025897131) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/44962994960#summary-137025897121) | CPU ms/turn, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/44962994960#summary-137025897192) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/44962994960#summary-137025897131) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/44962994960#summary-137025897121) | peak MB, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/44962994960#summary-137025897192) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/44962994960#summary-137025897131) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/44962994960#summary-137025897121) | install MB, macOS / Linux / Windows |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Crush | Go | 161 | 130 | 221398 | 0.0 | -0.0 | -0.5 | 274 | 281 | 192 | 139 / 141 / 141 |
| **Chanto** | Rust | **31** | **9** | **31** | **2.6** | **2.2** | **4.3** | **18** | **23** | **18** | 21 / 25 / 30 |
| jcode | Rust | 126 | 33 | 109 | 7.7 | 4.6 | 11.7 | 47 | 72 | 28 | 161 / 191 / 153 |
| Grok Build | Rust | 356 | 662 | 781 | 9.9 | 5.1 | 25.8 | 114 | 243 | 63 | 191 / 208 / 187 |
| Goose | Rust | 750 | 413 | 609 | 17.8 | 7.8 | 20.3 | 188 | 171 | 102 | 182 / 213 / 176 |
| Pi | Node | 462 | 373 | 648 | 10.6 | 8.1 | 12.3 | 178 | 157 | 141 | 169 / 176 / 123 |
| Forge | Rust | 242 | 190 | 859 | 12.2 | 10.3 | 19.1 | 88 | 82 | 87 | 111 / 131 / 98 |
| DeepSeek-Reasonix | Go | 191 | 165 | 750 | 9.5 | 14.3 | 17.4 | 72 | 81 | 67 | 49 / 53 / 58 |
| oh-my-pi | Bun | 1095 | 1521 | 2219 | 13.6 | 18.3 | 28.7 | 364 | 424 | 333 | 236 / 304 / 265 |
| mini-swe-agent | Python | 2619 | 3002 | 4953 | 29.6 | 19.2 | 74.0 | 247 | 240 | 254 | 497 / 610 / 448 |
| Gemini CLI | Node | 2240 | 1876 | 3469 | 30.3 | 22.4 | 34.4 | 503 | 470 | 388 | 105 / 105 / 112 |
| Codewhale | Rust | 626 | 184 | 1148 | 45.8 | 24.4 | 36.9 | 138 | 236 | 178 | 90 / 110 / 135 |
| Qwen Code | Node | 1641 | 1523 | 4703 | 42.5 | 24.7 | 123.7 | 233 | 229 | 427 | 285 / 324 / 206 |
| Mistral Vibe | Python | 2796 | 2873 | 5367 | 38.5 | 30.2 | 59.0 | 312 | 301 | 302 | 298 / 439 / 267 |
| Claude Code | Node | 549 | 398 | 906 | 56.7 | 39.0 | 58.2 | 374 | 320 | 306 | 364 / 381 / 388 |
| Open Interpreter | Rust | 88 | 107 | 180 | 15.6 | 45.4 | 593.9 | 98 | 304 | 151 | 251 / 299 / 340 |
| Continue CLI | Node | 1743 | 1191 | 1852 | 65.9 | 45.8 | 71.7 | 336 | 308 | 222 | 83 / 84 / 86 |
| opencode | Bun | 2950 | 2534 | 3422 | 66.7 | 47.2 | 66.6 | 614 | 573 | 558 | 226 / 253 / 260 |
| Codex | Rust | 430 | 388 | 484 | 57.1 | 50.8 | 806.4 | 158 | 223 | 248 | 395 / 444 / 540 |
| Cline | Node | 2119 | 1446 | 2789 | 70.7 | 68.2 | 79.7 | 706 | 673 | 614 | 381 / 435 / 333 |
| OpenHands | Python | 6113 | 6645 | 14141 | 75.7 | 77.8 | 328.9 | 356 | 346 | 472 | 485 / 523 / 423 |
| Kilo Code | Node | 8744 | 7322 | 10562 | 177.3 | 98.5 | 249.6 | 901 | 873 | 731 | 379 / 1,402 / 677 |
| Aider | Python | 3396 | 2913 | 4945 | 148.6 | 142.0 | 190.7 | 332 | 316 | 288 | 692 / 610 / 526 |

An instant mock model answers every request with a tool call that reads the
next 40 KB file, for 40 turns, so the context keeps growing. **Startup** is the
CPU of a run that makes one model request and exits. **CPU per turn** is the
rest of a full run's CPU, startup taken out, over the requests after the
first; before this run the table had one figure that mixed the two, so an
agent slow to start looked costly on every turn. CPU is user + sys time of the
agent's whole process tree; peak memory is the largest resident set of that
tree, sampled every 60 ms; install MB is what the pinned install puts on disk
(Node and Python, where needed, aren't counted). Sorted by Linux CPU per turn.
Raw files, with every run's numbers: [`results/overhead-20261122-012751.txt`](results/overhead-20261122-012751.txt)
(macOS), [`results/overhead-20261122-012040.txt`](results/overhead-20261122-012040.txt)
(Linux), and [`results/overhead-20261122-015131.txt`](results/overhead-20261122-015131.txt)
(Windows).

Notes on what isn't like for like are in [RESULTS.md](RESULTS.md#overhead-23-agents-startup-and-per-turn-mock-model-november-22).

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
