# Chanto benchmarks

Benchmarks for [Chanto](https://github.com/chanto-sh/chanto): coding tasks with
automated checks, a runner that drives Chanto and other coding agents on the
same model, and every raw result behind the published numbers.

- [RESULTS.md](RESULTS.md): results, with the versions and files behind each table
- [AUDIT.md](AUDIT.md): what a run records and how to check a result yourself

## Overhead: latest results

Measured November 24, 2026 by the [reproduce workflow, run 45484034964](https://github.com/chanto-sh/benchmarks/actions/runs/45484034964)
on GitHub's own runners: `python3 reproduce.py`, the 23
coding agents with at least 5,000 GitHub stars, each run 10 times; the table
shows medians. Each number is in the summary of that run, under its OS.

- **macOS**: `macos-latest`, Apple M1 (Virtual), 3 cores, 7 GB RAM, macOS (Darwin 25.6.0), arm64
- **Linux**: `ubuntu-latest`, AMD EPYC 9V74, 4 cores, 16 GB RAM, Linux 7.0 (Azure), x86_64
- **Windows**: `windows-latest`, AMD EPYC 7763, 4 cores, 16 GB RAM, Windows Server 2025, AMD64

Versions: Chanto 0.1.27; Aider 0.86.2; Claude Code 2.1.331; Cline 3.0.75; Codewhale 0.10.4; Codex 0.172.0; Continue CLI 1.5.47; Crush 0.102.0; DeepSeek-Reasonix 2.61.0; Forge 2.13.21; Gemini CLI 0.71.1; Goose 1.60.2; Grok Build 1.0.92; jcode 1.0.3; Kilo Code 7.8.32; mini-swe-agent 2.4.6; Mistral Vibe 3.1.5; oh-my-pi 19.1.1; Open Interpreter 0.0.61; OpenHands CLI 1.16.0; opencode 2.4.1; Pi 1.6.0; Qwen Code 0.28.4. The model is a local mock (`stressmock.py`), not a real one.

| agent | runtime | startup ms, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/45484034964#summary-138764961393) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/45484034964#summary-138764961425) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/45484034964#summary-138764961373) | CPU ms/turn, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/45484034964#summary-138764961393) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/45484034964#summary-138764961425) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/45484034964#summary-138764961373) | peak MB, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/45484034964#summary-138764961393) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/45484034964#summary-138764961425) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/45484034964#summary-138764961373) | install MB, macOS / Linux / Windows |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **Chanto** | Rust | **17** | **12** | **55** | **2.3** | **3.0** | **3.7** | **18** | **24** | **18** | 26 / 30 / 36 |
| jcode | Rust | 162 | 38 | 102 | 9.3 | 6.0 | 12.1 | 46 | 73 | 28 | 162 / 154 / 154 |
| Grok Build | Rust | 434 | 830 | 750 | 12.1 | 7.2 | 26.4 | 115 | 254 | 70 | 191 / 208 / 187 |
| Pi | Node | 649 | 491 | 656 | 14.5 | 10.5 | 10.5 | 177 | 164 | 142 | 169 / 176 / 123 |
| Goose | Rust | 318 | 535 | 641 | 12.2 | 11.1 | 20.5 | 187 | 168 | 103 | 182 / 213 / 176 |
| Codewhale | Rust | 493 | 173 | 1391 | 15.4 | 11.3 | 23.4 | 160 | 301 | 146 | 124 / 151 / 192 |
| Forge | Rust | 337 | 247 | 836 | 13.2 | 12.9 | 19.9 | 87 | 81 | 88 | 111 / 131 / 98 |
| Crush | Go | 573 | 347 | 664 | 32.0 | 18.6 | 15.2 | 180 | 179 | 145 | 139 / 141 / 141 |
| oh-my-pi | Bun | 1322 | 1476 | 2117 | 21.7 | 20.0 | 26.4 | 365 | 397 | 315 | 233 / 301 / 261 |
| DeepSeek-Reasonix | Go | 222 | 171 | 828 | 11.1 | 21.4 | 15.8 | 73 | 81 | 69 | 49 / 53 / 58 |
| mini-swe-agent | Python | 3031 | 3636 | 5062 | 37.6 | 22.5 | 74.8 | 247 | 241 | 254 | 498 / 610 / 448 |
| Gemini CLI | Node | 2918 | 2371 | 3430 | 34.5 | 28.2 | 36.7 | 502 | 472 | 388 | 128 / 128 / 135 |
| Qwen Code | Node | 2138 | 1945 | 4688 | 43.1 | 30.8 | 119.7 | 233 | 229 | 425 | 285 / 324 / 206 |
| Mistral Vibe | Python | 3625 | 3628 | 5516 | 36.5 | 40.6 | 61.7 | 313 | 304 | 308 | 291 / 445 / 269 |
| Claude Code | Node | 819 | 451 | 758 | 72.3 | 49.2 | 59.0 | 342 | 315 | 301 | 382 / 399 / 406 |
| Open Interpreter | Rust | 124 | 134 | 188 | 19.8 | 56.8 | 606.1 | 98 | 286 | 150 | 251 / 299 / 340 |
| Continue CLI | Node | 2062 | 1486 | 1867 | 85.9 | 57.2 | 69.5 | 336 | 308 | 222 | 83 / 84 / 86 |
| Codex | Rust | 529 | 633 | 500 | 47.7 | 59.6 | 764.3 | 154 | 224 | 249 | 401 / 450 / 549 |
| opencode | Bun | 2880 | 3513 | 3570 | 57.2 | 62.5 | 59.4 | 565 | 510 | 496 | 240 / 275 / 278 |
| Cline | Node | 2513 | 1998 | 2750 | 95.6 | 80.9 | 83.4 | 732 | 646 | 620 | 381 / 435 / 333 |
| OpenHands | Python | 10043 | 8033 | 14133 | 118.3 | 102.0 | 323.7 | 361 | 347 | 473 | 486 / 525 / 425 |
| Kilo Code | Node | 16193 | 8757 | 10484 | 211.4 | 123.8 | 251.8 | 915 | 836 | 729 | 379 / 1,402 / 677 |
| Aider | Python | 6646 | 3602 | 4930 | 307.9 | 181.0 | 197.3 | 326 | 316 | 287 | 690 / 610 / 526 |

An instant mock model answers every request with a tool call that reads the
next 40 KB file, for 40 turns, so the context keeps growing. **Startup** is the
CPU of a run that makes one model request and exits. **CPU per turn** is the
rest of a full run's CPU, startup taken out, over the requests after the
first; before this run the table had one figure that mixed the two, so an
agent slow to start looked costly on every turn. CPU is user + sys time of the
agent's whole process tree; peak memory is the largest resident set of that
tree, sampled every 60 ms; install MB is what the pinned install puts on disk
(Node and Python, where needed, aren't counted). Sorted by Linux CPU per turn.
Raw files, with every run's numbers: [`results/overhead-20261124-212047.txt`](results/overhead-20261124-212047.txt)
(macOS), [`results/overhead-20261124-210802.txt`](results/overhead-20261124-210802.txt)
(Linux), and [`results/overhead-20261124-213611.txt`](results/overhead-20261124-213611.txt)
(Windows).

Notes on what isn't like for like are in [RESULTS.md](RESULTS.md#overhead-23-agents-startup-and-per-turn-mock-model-november-24).

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
