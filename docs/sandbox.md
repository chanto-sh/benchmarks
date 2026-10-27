# Isolation, sandbox and timeouts

```sh
python3 run.py --agents chanto --tasks 'swe-*'     # isolated: the default
python3 -m unittest -v test_run
# Also run one fake agent under the real sandbox (no model needed):
BENCH_SANDBOX_SMOKE=1 python3 -m unittest -v test_run
```

Every task run is isolated by default: one agent, one task, one repetition,
in its own root, inside an OS sandbox. The goal is that a run sees only its own
task, so nothing it can reach on the machine or the network tells it the
answer. Import, setup and grading run outside the sandbox.

Before this, runs shared one work folder and config home per agent, and the
`--offline` sandbox only hid a list of known places. Transcripts from the
October 2026 hard tier show agents listing other agents' workspaces, reading
package caches and other environments, running `pip download` for a newer
release, digging in git history (`git fsck --lost-found`), fetching the upstream
fix from GitHub and searching the whole disk (`find /`). Any of these can
inflate a solve rate, so the tables measured that way are labelled in
[RESULTS.md](../RESULTS.md).

## One root per run

Each run gets a fresh root with a random name, `$BENCH_WORK/runs/r-XXXXXXXX/`:

- `<task>-<rep>/`: the task's checkout, where the agent starts,
- `home/`: the agent's `HOME`, with `XDG_*`, `CARGO_HOME` and `GOPATH` inside
  it; the agent's config (provider, model, permissions) is written here,
- `tmp/`: `TMPDIR` (and `TMUX_TMPDIR`).

The agent's runtimes still work from their real locations: `RUSTUP_HOME`,
`VOLTA_HOME`, `NVM_DIR` and `PYENV_ROOT` point at the real ones (read-only), and
the node binary behind a Volta shim goes first on `PATH`. git uses a neutral
identity and no system or user config.

After grading, the root is deleted. The transcript and the patch stay in
`$BENCH_WORK/<agent>/<task>-<rep>.out` and `.patch`, and the evidence (with the
agent's session files) goes next to the result file as before.
`BENCH_KEEP_WORK=1` keeps roots for debugging.

## The task checkout

The checkout ends at the task's starting point. SWE-bench tasks are cloned from
a local bare mirror and checked out at the base commit, and then their `.git` is
replaced by a fresh repository with one commit of the base tree
(`import_swebench.py`). After every setup, `seal_checkout` removes remotes,
alternates, every ref but the current branch, reflogs, `FETCH_HEAD` and
`ORIG_HEAD`, and runs `git gc --prune=now`. It then checks that every object
left is reachable from the current branch, and fails the setup if not. So
`git log --all`, `git fsck --lost-found` and `git cat-file --batch-all-objects`
find nothing past the base commit.

## Packages

A SWE-bench task's virtualenv is built in its checkout before the clock starts,
with the pinned dependencies, and the agent gets it on `PATH`. Package managers
point at nothing: `PIP_NO_INDEX=1` and an unreachable `PIP_INDEX_URL`,
`UV_OFFLINE=1`, an unreachable npm registry, `GOPROXY=off`,
`CARGO_NET_OFFLINE=true`, and the Hugging Face libraries offline. A task's
declared Rust crates are fetched into the run's own `CARGO_HOME` before the
agent starts. So an agent can't install a newer release of the package under
test, even where the sandbox couldn't stop the download.

## The sandbox

| | macOS (`sandbox-exec`) | Linux (bubblewrap and socat) |
|---|---|---|
| Reads | Denied by default. Allowed: the run root, the agent's own install, system paths (`/System`, `/usr`, `/bin`, `/sbin`, `/Library`, `/opt/homebrew`, `/private/etc`, Xcode) and language runtimes (version managers under `HOME`, the install prefix of `node`, `python3`, `git`, `go`, `cargo` and `uv` on `PATH`, and `BENCH_TOOLCHAINS`) | A new, empty root filesystem. Mounted read-only: `/usr`, `/bin`, `/sbin`, `/lib*`, `/etc`, `/opt`, `/nix/store`, the same runtimes and the agent's own install. Nothing else exists |
| Writes | Only the run root and `/dev` | Only the run root, and a private `/tmp` and `/var/tmp` that are thrown away |
| Hidden even inside allowed paths | This repository (and any checkout of it, by folder name), the Chanto sources, `~/.local/share/chanto-bench`, `~/.cache/chanto-bench`, and the pip, uv and Hugging Face caches | The same, covered by empty mounts |
| Installed Python packages (SWE-bench tasks) | Every `site-packages` and `dist-packages` outside the run root and the agent's install | The same, covered by empty mounts |
| Network | Outbound only to `localhost`, inbound only on `localhost`; Unix sockets only for DNS and inside the run root | Its own network namespace: only the model proxy and meter ports are bridged in; servers a task's tests start work inside it |
| Other | No Apple Events and no LaunchServices opens, so an agent can't ask a browser or another app to fetch something | Its own PID and IPC namespaces: whatever the agent leaves running dies with it |

Each agent can read its own install and no other's. Chanto's own sandbox is
turned off for the run, since it would nest inside this one.

Every agent the runner knows was started under the macOS profile, each in its
own run root and HOME, and each finished a short session against the local mock
model (`stressmock.py`, no real model): Rust (Chanto, Codex, Goose, Codewhale,
Forge), Node (Claude Code, Gemini CLI, Qwen Code, Pi, Kilo Code, Cline,
Continue), Bun (opencode), Go (Crush), Python (Aider, OpenHands), and zerostack
and hax. None needed `~/.config` or the keychain once it had its own HOME. The
Linux sandbox is exercised in CI by the smoke test.

### What it doesn't stop

- **The model.** It may have seen the fix in training. Nothing here can change
  that.
- **The proxy.** The agent reaches the model proxy, and the proxy reaches the
  provider. Only model requests go through it, but if the proxy is set up with
  provider-side tools (web search), those run outside the sandbox.
- **Other local services, on macOS.** `sandbox-exec` can allow localhost but
  not single ports, and a task's own tests start servers on localhost. Any
  service listening on localhost is reachable, so don't run a local HTTP proxy
  to the internet on the benchmark machine. On Linux only the proxy and meter
  ports are bridged in.
- **Names, on macOS.** File metadata (`stat`) is allowed everywhere, and the
  run root's parent folders can be listed by name, because `getcwd` needs it.
  So an agent can see that `~/IdeaProjects` or a sibling `r-XXXXXXXX` exists,
  but can't list or read anything inside it. On Linux those folders don't
  exist in the agent's view.
- **System and toolchain paths.** They're readable on both. They hold no task
  data, but anything else kept under them is visible, and a runtime installed
  somewhere unusual has to be named in `BENCH_TOOLCHAINS`.
- **The agent's own install.** An agent has to read its own environment to run.
  A Python agent's environment (Aider, OpenHands) holds its own, newer
  `requests` and similar libraries, which can contain the upstream fix for a
  `psf/requests` task. The detector flags reads of installed packages' files.
- **macOS system services.** Apple Events and LaunchServices are denied; other
  system services that a process can talk to over Mach IPC are not. None is a
  known way to the network or to files, but that isn't proven.
- **Linux prerequisites.** bubblewrap needs unprivileged user namespaces
  (Ubuntu 24.04 restricts them: `sysctl kernel.apparmor_restrict_unprivileged_userns=0`).
  Without bwrap and socat the runner refuses to start rather than run unisolated.
- **Other platforms.** There's no sandbox for Windows; the runner refuses to
  start there unless isolation is turned off.

## Detecting off-task access

The sandbox stops most attempts, but not everything above. So after each run
the runner reads the transcript and the agent's own session files and records
what it reached for outside its task as `offtask_hits` in the result, a list of
`{kind, text}`:

| kind | what it matches |
|---|---|
| `bench data` | `chanto-bench`, `work-hard-*`, `harness-verify`, another run's `runs/r-XXXXXXXX` or config home |
| `path outside run root` | an absolute path under `/Users`, `/home`, `/root`, `/private`, `/var`, `/opt`, `/mnt`, `/Volumes`, `/srv` or `/data` that isn't the run root, a runtime, an agent install or scratch space (`/tmp`) |
| `installed package` | a file in a `site-packages` or `dist-packages` folder outside the run root |
| `package download` | `pip download`, `pip index`, `pip install --upgrade`, `pip install` from a URL, `uv pip install` |
| `package host` | `pypi.org`, `files.pythonhosted.org` |
| `git history` | `git fsck`, `fetch`, `clone`, `pull`, `remote add`, `--lost-found`, `--batch-all-objects`, `git log --all` |
| `whole-disk search` | `find /`, `fd /`, `rg /`, `grep -r /`, `ls -R /`, `du /`, `mdfind`, `locate` |
| `web` | a GitHub pull request, commit, compare view or file URL, or the GitHub API |
| `upstream repo` | any GitHub URL of a SWE-bench task's upstream repository |

URLs quoted in the task's own prompt don't count, and neither do the run's own
paths, even when an agent prints them wrapped over two lines. What agents fetch
for themselves at startup (OpenHands' skills, LiteLLM's price list) is left out.
It's a pattern match, so read a run's hits before calling it contaminated: on
an isolated run most hits are failed attempts. `--report` marks runs with hits
⚠ and counts them per agent.

## Turning it off

`CHANTO_BENCH_ISOLATION=off` runs agents without the sandbox, for debugging
only. Each run still gets its own root, HOME and sealed checkout. The result
file records `"isolation": "off"` (otherwise `sandbox-exec` or `bwrap`; it's
also in `meta.isolation` and in each run's entry), the runner warns when it
starts, and `run.py --report` refuses to tabulate such files, or files from
before isolation was recorded. `--report --unisolated` shows them anyway,
labelled as measured without isolation and not for publishing. `--offline` is
still accepted and means the default.

## Processes and timeouts

Agent, setup and grading commands each run in their own process group. After
the agent exits or times out, the runner kills what's left in its group, and
anything still running inside its run root, before grading. Children that start
their own session or process group escape the group cleanup; on Linux the PID
namespace ends them with the agent.

- Agent timeout: the result records `timed_out: true` and `exit_code: -1`.
- Grading timeout: exit code 124 with a timeout message.
- SWE tasks: 1800 seconds for the agent (`--timeout` overrides), 600 for setup
  (not counted as agent time) and 600 for grading.
