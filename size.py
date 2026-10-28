#!/usr/bin/env python3
"""Install size of each compared agent: what its pinned install puts on disk.

    python3 size.py [agents...]       # writes results/size-<date>.txt

Measured from the benchmark's own installs (install-agents.sh), the same ones
cputurn.py runs:
  - native binaries (Chanto, Goose, opencode, Codewhale, zerostack, hax): the
    executable;
  - npm agents: the agent's package plus every dependency it pulls in, walked
    through agents/package-lock.json with Node's resolution rules and measured
    in one `du` pass, so a file npm links into two places counts once;
  - Python agents: their uv tool environment.
Node and Python themselves aren't counted; agents that need them are marked.
Forge's npm package carries an executable for every platform; only the one
for this machine counts.
"""
import importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("benchrun", ROOT / "run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)

CHANTO_BIN = Path(os.environ.get("BENCH_CHANTO_BIN", run.CHANTO_REPO / "target" / "release" / "chanto"))
NPM_ROOT = run.NPM_BIN.parent.parent

# agent -> (display name, runtime, how it's installed, npm package or path)
AGENTS = {
    "chanto": ("Chanto", "Rust", "bin", CHANTO_BIN),
    "forge": ("Forge", "Rust", "npm", "@antinomyhq/forge"),
    "pi": ("Pi", "Node", "npm", "@earendil-works/pi-coding-agent"),
    "goose": ("Goose", "Rust", "bin", run.BIN_DIR / "goose"),
    "crush": ("Crush", "Go", "npm", "@charmland/crush"),
    "claude": ("Claude Code", "Node", "npm", "@anthropic-ai/claude-code"),
    "qwen": ("Qwen Code", "Node", "npm", "@qwen-code/qwen-code"),
    "codex": ("Codex", "Rust", "npm", "@openai/codex"),
    "cline": ("Cline", "Node", "npm", "cline"),
    "cn": ("Continue CLI", "Node", "npm", "@continuedev/cli"),
    "opencode": ("opencode", "Bun", "bin", run.BIN_DIR / "opencode"),
    "aider": ("Aider", "Python", "uv", run.UV_TOOLS / "aider-chat"),
    "kilo": ("Kilo Code", "Node", "npm", "@kilocode/cli"),
    "openhands": ("OpenHands", "Python", "uv", run.UV_TOOLS / "openhands"),
    "codewhale": ("Codewhale", "Rust", "bin", run.BIN_DIR / "codewhale"),
    "zerostack": ("zerostack", "Rust", "bin", run.BIN_DIR / "zerostack"),
    "hax": ("hax", "C", "bin", run.BIN_DIR / "hax"),
    "gemini": ("Gemini CLI", "Node", "npm", "@google/gemini-cli"),
    "jcode": ("jcode", "Rust", "bin", run.BIN_DIR / "jcode"),
    "reasonix": ("DeepSeek-Reasonix", "Go", "bin", run.BIN_DIR / "reasonix"),
    "omp": ("oh-my-pi", "Bun", "bin", run.BIN_DIR / "omp"),
    "interpreter": ("Open Interpreter", "Rust", "bin", run.BIN_DIR / "interpreter"),
    "grok": ("Grok Build", "Rust", "bin", run.BIN_DIR / "grok"),
    "fx": ("fx", "Zig", "bin", run.BIN_DIR / "fx"),
    "mini": ("mini-swe-agent", "Python", "uv", run.UV_TOOLS / "mini-swe-agent"),
    "vibe": ("Mistral Vibe", "Python", "uv", run.UV_TOOLS / "mistral-vibe"),
}
# Agents whose install runs on a separately installed runtime. The others
# (Claude Code and Kilo Code included) ship their runtime inside the executable.
NEEDS = {"pi": "Node", "qwen": "Node", "cline": "Node", "cn": "Node", "gemini": "Node", "aider": "Python",
         "openhands": "Python"}
FORGE_PLATFORM = {("Darwin", "arm64"): "darwin/arm64", ("Darwin", "x86_64"): "darwin/x64",
                  ("Linux", "aarch64"): "linux/arm64", ("Linux", "x86_64"): "linux/x64"}


def du_bytes(paths):
    """Disk usage of `paths` together, each hard-linked file counted once."""
    out = subprocess.run(["du", "-skc", *map(str, paths)], capture_output=True, text=True, check=True).stdout
    return int(out.strip().splitlines()[-1].split()[0]) * 1024


def npm_closure(pkg, lock):
    """node_modules paths of `pkg` and everything it requires, resolved the way
    Node does: the nearest node_modules walking up from the requiring package."""
    def resolve(name, frm):
        base = frm
        while True:
            cand = (base + "/" if base else "") + "node_modules/" + name
            if cand in lock:
                return cand
            if not base:
                return None
            i = base.rfind("/node_modules/")
            base = base[:i] if i >= 0 else ""

    seen, stack = set(), [resolve(pkg, "")]
    while stack:
        p = stack.pop()
        if not p or p in seen or not (NPM_ROOT / p).exists():
            continue
        seen.add(p)
        e = lock[p]
        for dep in [*e.get("dependencies", {}), *e.get("optionalDependencies", {})]:
            stack.append(resolve(dep, p))
    # Nested node_modules are inside their parent's directory already.
    return [p for p in seen if not any(p != q and p.startswith(q + "/") for q in seen)]


def other_platform_bytes(pkg_dir):
    """Bytes of Forge's executables for platforms other than this one."""
    mine = FORGE_PLATFORM.get((platform.system(), platform.machine()))
    total = 0
    for dirpath, _, files in os.walk(pkg_dir / "bin"):
        if mine and mine in dirpath:
            continue
        total += sum(os.lstat(os.path.join(dirpath, f)).st_blocks * 512 for f in files)
    return total


def measure(agent, lock):
    _, _, kind, where = AGENTS[agent]
    if kind == "npm":
        paths = npm_closure(where, lock)
        size = du_bytes([NPM_ROOT / p for p in paths])
        if agent == "forge":
            size -= other_platform_bytes(NPM_ROOT / "node_modules" / where)
        return size, f"{len(paths)} npm packages"
    path = Path(where).resolve()
    return du_bytes([path]), str(where).replace(str(Path.home()), "~")


def runtime_sizes():
    """Size of the Node and Python the agents above would run on, for reference."""
    out = {}
    node = subprocess.run(["node", "-p", "process.execPath"], capture_output=True, text=True).stdout.strip()
    if node:
        out["Node"] = (os.path.getsize(node), f"node {run.first_line(['node', '--version'])}")
    py = run.UV_TOOLS / "aider-chat" / "bin" / "python"
    if py.exists():
        home = py.resolve().parent.parent
        out["Python"] = (du_bytes([home]), home.name)
    return out


def version(agent):
    if agent == "chanto":
        return run.first_line([str(CHANTO_BIN), "--version"])
    return run.first_line(run.VERSION_CMDS[agent]) if agent in run.VERSION_CMDS else "unknown"


def main():
    agents = sys.argv[1:] or list(AGENTS)
    lock = json.loads((NPM_ROOT / "package-lock.json").read_text())["packages"]
    rows = []
    for a in agents:
        size, what = measure(a, lock)
        rows.append((a, size, what))
    rows.sort(key=lambda r: r[1])
    mb = lambda b: b / 1e6
    machine = run.first_line(["sysctl", "-n", "hw.model"]) if platform.system() == "Darwin" else platform.node()
    lines = [
        "# size.py: what each agent's pinned install puts on disk",
        f"# command: python3 size.py {' '.join(sys.argv[1:])}".rstrip(),
        f"# machine: {machine}, {platform.system()} {platform.release()} {platform.machine()}",
        *[f"# {a}: {version(a)} ({AGENTS[a][3] if AGENTS[a][2] == 'npm' else what})" for a, _, what in rows],
        f"# date: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "",
        f"{'agent':<14}{'runtime':<9}{'install MB':>11}  needs",
        "-" * 44,
        *[f"{AGENTS[a][0]:<14}{AGENTS[a][1]:<9}{mb(s):>11.1f}  {NEEDS.get(a, '')}" for a, s, _ in rows],
        "",
        "Runtimes, not included above:",
        *[f"  {k:<8}{mb(s):>7.1f} MB  ({w})" for k, (s, w) in runtime_sizes().items()],
        "MB = 10^6 bytes of disk usage (du). npm sizes include each agent's dependencies.",
    ]
    text = "\n".join(lines) + "\n"
    print(text, end="")
    out = run.RESULTS / f"size-{time.strftime('%Y%m%d-%H%M%S')}.txt"
    out.write_text(text)
    print(f"\nsaved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
