# Chanto benchmarks

Benchmarks for [Chanto](https://github.com/chanto-sh/chanto): coding tasks with
automated checks, a runner that drives Chanto and other coding agents on the
same model, and every raw result behind the published numbers.

- [RESULTS.md](RESULTS.md): results, with the versions and files behind each table
- [AUDIT.md](AUDIT.md): what a run records and how to check a result yourself

## Overhead: latest results

Measured October 31, 2026 by the [reproduce workflow, run 41176862324](https://github.com/chanto-sh/benchmarks/actions/runs/41176862324)
on GitHub's own runners, from [#14](https://github.com/chanto-sh/benchmarks/pull/14): `python3 reproduce.py`, the 23
coding agents with at least 5,000 GitHub stars, each run 10 times; the table
shows medians. Each number is in the summary of that run, under its OS.

- **macOS**: `macos-latest`, Apple M1 (Virtual), 3 cores, 7 GB RAM, macOS (Darwin 25.6.0), arm64
- **Linux**: `ubuntu-latest`, Intel Xeon Platinum 8573C, 4 cores, 16 GB RAM, Linux 7.0 (Azure), x86_64
- **Windows**: `windows-latest`, AMD EPYC, 4 cores, 16 GB RAM, Windows Server 2025, AMD64, measured separately in [run 41224112845](https://github.com/chanto-sh/benchmarks/actions/runs/41224112845), with OpenHands from [run 41227780887](https://github.com/chanto-sh/benchmarks/actions/runs/41227780887) and mini-swe-agent from [run 41228735404](https://github.com/chanto-sh/benchmarks/actions/runs/41228735404)

GitHub gave this run's Linux job an Intel Xeon where earlier runs had AMD EPYC
chips, so compare agents within one run, not across runs.

Versions: Chanto 0.1.10; Aider 0.86.2; Claude Code 2.1.302; Cline 3.0.70; Codewhale 0.10.1; Codex 0.162.1; Continue CLI 1.5.47; Crush 0.98.1; DeepSeek-Reasonix 2.54.0; Forge 2.13.21; Gemini CLI 0.65.0; Goose 1.54.0; Grok Build 1.0.70; jcode 0.99.1; Kilo Code 7.8.8; mini-swe-agent 2.4.6; Mistral Vibe 3.0.3; oh-my-pi 18.13.3; Open Interpreter 0.0.56; OpenHands CLI 1.16.0; opencode 2.0.22; Pi 1.1.0; Qwen Code 0.25.1. The model is a local mock (`stressmock.py`), not a real one.

| agent | runtime | startup ms, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/41176862324#summary-124466111397) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/41176862324#summary-124466111535) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/41224112845#summary-124604558328) | CPU ms/turn, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/41176862324#summary-124466111397) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/41176862324#summary-124466111535) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/41224112845#summary-124604558328) | peak MB, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/41176862324#summary-124466111397) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/41176862324#summary-124466111535) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/41224112845#summary-124604558328) | install MB, macOS / Linux / Windows |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **Chanto** | Rust | **13** | **23** | **78** | **1.5** | **3.1** | **3.1** | **17** | **24** | **19** | 20 / 24 / 29 |
| Goose | Rust | 222 | 392 | 609 | 4.2 | 5.8 | 17.4 | 171 | 153 | 88 | 269 / 308 / 250 |
| Grok Build | Rust | 372 | 492 | 781 | 6.7 | 6.1 | 21.1 | 109 | 225 | 61 | 179 / 196 / 176 |
| Pi | Node | 295 | 542 | 664 | 6.0 | 9.1 | 11.5 | 179 | 155 | 143 | 158 / 164 / 114 |
| jcode | Rust | 109 | 36 | 125 | 9.2 | 10.6 | 16.4 | 49 | 73 | 32 | 143 / 171 / 135 |
| Forge | Rust | 138 | 196 | 820 | 7.0 | 11.4 | 19.5 | 87 | 81 | 86 | 111 / 131 / 98 |
| Crush | Go | 209 | 279 | 578 | 16.4 | 14.4 | 14.1 | 179 | 171 | 143 | 130 / 132 / 131 |
| DeepSeek-Reasonix | Go | 189 | 255 | 805 | 10.3 | 16.6 | 21.3 | 76 | 86 | 72 | 51 / 54 / 59 |
| oh-my-pi | Bun | 908 | 1956 | 2344 | 11.9 | 17.6 | 23.6 | 361 | 385 | 308 | 217 / 277 / 245 |
| Qwen Code | Node | 1098 | 2122 | 4984 | 20.3 | 20.9 | 113.0 | 245 | 223 | 437 | 152 / 172 / 162 |
| mini-swe-agent | Python | 1952 | 3171 | 4133 | 27.9 | 25.1 | 61.6 | 229 | 211 | 239 | 460 / 577 / 415 |
| Gemini CLI | Node | 1268 | 2092 | 3344 | 21.3 | 28.9 | 51.2 | 527 | 519 | 420 | 105 / 105 / 112 |
| Codewhale | Rust | 236 | 206 | 1117 | 26.1 | 33.8 | 33.0 | 129 | 212 | 164 | 86 / 105 / 128 |
| Open Interpreter | Rust | 59 | 119 | 188 | 15.0 | 42.5 | 597.1 | 97 | 268 | 150 | 250 / 297 / 338 |
| Mistral Vibe | Python | 1578 | 2345 | 3875 | 27.5 | 42.7 | 68.9 | 251 | 234 | 243 | 219 / 372 / 204 |
| Claude Code | Node | 315 | 434 | 1023 | 32.4 | 46.4 | 55.9 | 377 | 336 | 337 | 268 / 566 / 290 |
| Codex | Rust | 259 | 515 | 484 | 30.2 | 46.6 | 755.9 | 199 | 262 | 251 | 338 / 453 / 457 |
| Continue CLI | Node | 764 | 1360 | 1906 | 38.3 | 49.2 | 75.0 | 334 | 308 | 223 | 83 / 84 / 86 |
| Cline | Node | 967 | 1812 | 2719 | 29.9 | 68.0 | 62.7 | 618 | 627 | 575 | 341 / 396 / 291 |
| opencode | Bun | 1111 | 2370 | 2625 | 42.3 | 79.6 | 90.2 | 528 | 483 | 491 | 180 / 204 / 207 |
| OpenHands | Python | 5488 | 7271 | 8656 | 85.0 | 98.3 | 205.6 | 341 | 320 | 456 | 626 / 620 / 519 |
| Kilo Code | Node | 4344 | 7730 | 9289 | 77.5 | 121.7 | 248.4 | 960 | 900 | 785 | 341 / 1,246 / 596 |
| Aider | Python | 3532 | 3289 | 4984 | 145.3 | 159.2 | 190.5 | 321 | 301 | 280 | 690 / 610 / 526 |

An instant mock model answers every request with a tool call that reads the
next 40 KB file, for 40 turns, so the context keeps growing. **Startup** is the
CPU of a run that makes one model request and exits. **CPU per turn** is the
rest of a full run's CPU, startup taken out, over the requests after the
first; before this run the table had one figure that mixed the two, so an
agent slow to start looked costly on every turn. CPU is user + sys time of the
agent's whole process tree; peak memory is the largest resident set of that
tree, sampled every 60 ms; install MB is what the pinned install puts on disk
(Node and Python, where needed, aren't counted). Sorted by Linux CPU per turn.
Raw files, with every run's numbers: [`results/overhead-20261031-064921.txt`](results/overhead-20261031-064921.txt)
(macOS), [`results/overhead-20261031-065121.txt`](results/overhead-20261031-065121.txt)
(Linux), and for Windows [`results/overhead-20261031-180439.txt`](results/overhead-20261031-180439.txt),
[`results/overhead-20261031-181631.txt`](results/overhead-20261031-181631.txt) (OpenHands) and
[`results/overhead-20261031-182303.txt`](results/overhead-20261031-182303.txt) (mini-swe-agent).

Notes on what isn't like for like are in [RESULTS.md](RESULTS.md#overhead-23-agents-startup-and-per-turn-mock-model-october-31).

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
