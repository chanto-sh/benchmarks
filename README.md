# Chanto benchmarks

Benchmarks for [Chanto](https://github.com/chanto-sh/chanto): coding tasks with
automated checks, a runner that drives Chanto and other coding agents on the
same model, and every raw result behind the published numbers.

- [RESULTS.md](RESULTS.md): results, with the versions and files behind each table
- [AUDIT.md](AUDIT.md): what a run records and how to check a result yourself

## Overhead: latest results

Measured November 25, 2026 by the [reproduce workflow, run 45522529572](https://github.com/chanto-sh/benchmarks/actions/runs/45522529572)
on GitHub's own runners: `python3 reproduce.py`, the 23
coding agents with at least 5,000 GitHub stars, each run 10 times; the table
shows medians. Each number is in the summary of that run, under its OS.

- **macOS**: `macos-latest`, Apple M1 (Virtual), 3 cores, 7 GB RAM, macOS (Darwin 25.6.0), arm64
- **Linux**: `ubuntu-latest`, Intel Xeon Platinum 8573C, 4 cores, 16 GB RAM, Linux 7.0 (Azure), x86_64
- **Windows**: `windows-latest`, AMD EPYC 7763, 4 cores, 16 GB RAM, Windows Server 2025, AMD64

Versions: Chanto 0.1.28; Aider 0.86.2; Claude Code 2.1.331; Cline 3.0.75; Codewhale 0.10.4; Codex 0.172.0; Continue CLI 1.5.47; Crush 0.102.0; DeepSeek-Reasonix 2.61.0; Forge 2.13.21; Gemini CLI 0.71.1; Goose 1.60.2; Grok Build 1.0.92; jcode 1.0.3; Kilo Code 7.8.32; mini-swe-agent 2.4.6; Mistral Vibe 3.1.5; oh-my-pi 19.1.1; Open Interpreter 0.0.61; OpenHands CLI 1.16.0; opencode 2.4.1; Pi 1.6.0; Qwen Code 0.28.4. The model is a local mock (`stressmock.py`), not a real one.

| agent | runtime | startup ms, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/45522529572#summary-138897932427) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/45522529572#summary-138897932411) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/45522529572#summary-138897932333) | CPU ms/turn, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/45522529572#summary-138897932427) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/45522529572#summary-138897932411) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/45522529572#summary-138897932333) | peak MB, [macOS](https://github.com/chanto-sh/benchmarks/actions/runs/45522529572#summary-138897932427) | [Linux](https://github.com/chanto-sh/benchmarks/actions/runs/45522529572#summary-138897932411) | [Windows](https://github.com/chanto-sh/benchmarks/actions/runs/45522529572#summary-138897932333) | install MB, macOS / Linux / Windows |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **Chanto** | Rust | **11** | **11** | **39** | **1.2** | **2.8** | **4.3** | **18** | **24** | **17** | 26 / 30 / 36 |
| jcode | Rust | 151 | 35 | 117 | 9.7 | 6.5 | 10.9 | 48 | 74 | 29 | 162 / 154 / 154 |
| Grok Build | Rust | 422 | 700 | 750 | 13.1 | 7.6 | 23.8 | 116 | 247 | 63 | 191 / 208 / 187 |
| Pi | Node | 466 | 454 | 680 | 10.4 | 10.3 | 11.5 | 171 | 164 | 142 | 169 / 176 / 123 |
| Goose | Rust | 276 | 430 | 617 | 8.3 | 11.4 | 23.0 | 190 | 164 | 103 | 182 / 213 / 176 |
| Forge | Rust | 265 | 194 | 797 | 13.5 | 12.2 | 19.9 | 86 | 81 | 86 | 111 / 131 / 98 |
| Codewhale | Rust | 475 | 150 | 1375 | 17.2 | 12.5 | 22.3 | 161 | 298 | 144 | 124 / 151 / 192 |
| DeepSeek-Reasonix | Go | 276 | 242 | 789 | 13.4 | 15.4 | 14.8 | 72 | 81 | 67 | 49 / 53 / 58 |
| Crush | Go | 326 | 317 | 602 | 22.9 | 15.9 | 13.3 | 177 | 179 | 146 | 139 / 141 / 141 |
| mini-swe-agent | Python | 3147 | 3706 | 4766 | 29.5 | 22.7 | 70.5 | 248 | 240 | 254 | 498 / 610 / 448 |
| Qwen Code | Node | 1701 | 1826 | 4641 | 40.4 | 27.0 | 124.6 | 232 | 229 | 425 | 285 / 324 / 206 |
| Gemini CLI | Node | 2174 | 2242 | 3383 | 33.6 | 27.2 | 36.1 | 502 | 471 | 388 | 128 / 128 / 135 |
| oh-my-pi | Bun | 1176 | 1753 | 2086 | 19.1 | 30.8 | 27.7 | 358 | 412 | 316 | 233 / 301 / 261 |
| Mistral Vibe | Python | 3378 | 3696 | 5414 | 48.4 | 43.7 | 60.0 | 314 | 304 | 305 | 284 / 445 / 269 |
| Claude Code | Node | 605 | 433 | 789 | 54.5 | 45.8 | 51.0 | 364 | 317 | 304 | 382 / 399 / 406 |
| Open Interpreter | Rust | 122 | 128 | 172 | 20.9 | 52.0 | 583.2 | 98 | 310 | 150 | 251 / 299 / 340 |
| Continue CLI | Node | 1458 | 1400 | 1867 | 63.2 | 55.0 | 71.3 | 335 | 308 | 221 | 83 / 84 / 86 |
| Codex | Rust | 396 | 425 | 461 | 50.8 | 58.0 | 759.0 | 153 | 227 | 247 | 401 / 450 / 549 |
| opencode | Bun | 2884 | 3338 | 3492 | 62.4 | 63.3 | 57.6 | 572 | 542 | 496 | 240 / 275 / 278 |
| Cline | Node | 1928 | 1868 | 2797 | 64.5 | 87.4 | 73.6 | 704 | 638 | 607 | 381 / 435 / 333 |
| OpenHands | Python | 9660 | 7786 | 13836 | 133.2 | 100.5 | 301.1 | 357 | 347 | 473 | 487 / 526 / 425 |
| Kilo Code | Node | 9165 | 8395 | 10312 | 126.3 | 129.1 | 248.6 | 895 | 835 | 754 | 379 / 1,402 / 677 |
| Aider | Python | 4641 | 3620 | 4773 | 202.0 | 161.3 | 192.7 | 326 | 314 | 289 | 691 / 610 / 526 |

An instant mock model answers every request with a tool call that reads the
next 40 KB file, for 40 turns, so the context keeps growing. **Startup** is the
CPU of a run that makes one model request and exits. **CPU per turn** is the
rest of a full run's CPU, startup taken out, over the requests after the
first; before this run the table had one figure that mixed the two, so an
agent slow to start looked costly on every turn. CPU is user + sys time of the
agent's whole process tree; peak memory is the largest resident set of that
tree, sampled every 60 ms; install MB is what the pinned install puts on disk
(Node and Python, where needed, aren't counted). Sorted by Linux CPU per turn.
Raw files, with every run's numbers: [`results/overhead-20261125-013007.txt`](results/overhead-20261125-013007.txt)
(macOS), [`results/overhead-20261125-012317.txt`](results/overhead-20261125-012317.txt)
(Linux), and [`results/overhead-20261125-015356.txt`](results/overhead-20261125-015356.txt)
(Windows).

Notes on what isn't like for like are in [RESULTS.md](RESULTS.md#overhead-23-agents-startup-and-per-turn-mock-model-november-25).

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
