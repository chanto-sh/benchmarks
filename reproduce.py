#!/usr/bin/env python3
"""Reproduce the published overhead numbers with one command.

    python3 reproduce.py             # every agent RESULTS.md compares (needs npm and uv)
    python3 reproduce.py --quick     # the native binaries only (needs curl and tar)
    python3 reproduce.py --agents chanto,hax,zerostack   # any subset, extras included

It installs each agent at the version RESULTS.md reports (install-agents.sh:
pinned, checksum-verified; Chanto as its release binary), drives each one
through the same file-reading task against a local mock model, and prints its
startup CPU, CPU per turn, peak memory and install size, with each agent's ratio
to Chanto. The mock answers instantly, so what's measured is the agent's own
work, and no API key or model is needed.

Startup and per-turn cost are separate columns: an agent that is slow to start
but cheap per turn, or the reverse, shows as such. Startup is the CPU of a run
that makes one model request and stops; per turn is the rest of a full run's
CPU spread over its other requests. A one-shot or CI run pays the first every
time, a long session mostly the second.

Absolute numbers depend on the machine; the ratios are what should carry over.
A copy of the table, with the versions, machine, settings and every rep's raw
numbers, goes to results/overhead-<date>.txt.
"""
import argparse, json, os, platform, shutil, statistics, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# The published configuration. Change it here and RESULTS.md cites this file.
TURNS = 40  # model requests per run, each asking to read one more file
BLOB_KB = 40  # size of each file (hax refuses files over 50 KB)
REPS = 10  # runs per agent; the table shows the median

# Every agent RESULTS.md compares (coding agents with at least 5,000 GitHub
# stars), and what installs it.
NATIVE = ["chanto", "goose", "codewhale", "opencode"]
NPM = ["forge", "pi", "crush", "claude", "qwen", "codex", "gemini", "cline", "cn", "kilo"]
UV = ["aider", "openhands"]
# Added after the October 25 table (each over 5,000 stars, except fx at 3,600,
# included for its native, small-footprint design): measured in every
# full run, but not in --quick, which stays the original four for speed.
NEW_NATIVE = ["jcode", "reasonix", "omp", "interpreter", "grok", "fx"]
NEW_UV = ["mini", "vibe"]
PUBLISHED = NATIVE + NPM + UV + NEW_NATIVE + NEW_UV
# Native agents that still run here but aren't in the published table, since
# they're below that bar: only measured when --agents names them.
EXTRA = ["hax", "zerostack"]
ALL = PUBLISHED + EXTRA


def sh(cmd, **kw):
    print(f"$ {' '.join(map(str, cmd))}", flush=True)
    subprocess.run(cmd, check=True, **kw)


def machine():
    """The CPU and memory, never the host name."""
    if platform.system() == "Darwin":
        q = lambda k: subprocess.run(["sysctl", "-n", k], capture_output=True, text=True).stdout.strip()
        cpu = f"{q('machdep.cpu.brand_string')} ({q('hw.model')}), {q('hw.ncpu')} cores"
        mem = int(q("hw.memsize") or 0)
    elif platform.system() == "Windows":
        import ctypes, winreg

        class Memory(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_uint32), ("dwMemoryLoad", ctypes.c_uint32)] + \
                       [(n, ctypes.c_uint64) for n in ("total", "avail", "pagefile", "availPagefile",
                                                       "virtual", "availVirtual", "availExtended")]
        m = Memory(dwLength=ctypes.sizeof(Memory))
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        mem = m.total
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                name = winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except OSError:
            name = platform.processor() or "unknown CPU"
        cpu = f"{name}, {os.cpu_count()} cores"
    else:
        info = Path("/proc/cpuinfo").read_text() if Path("/proc/cpuinfo").exists() else ""
        names = [l.split(":", 1)[1].strip() for l in info.splitlines() if l.lower().startswith(("model name", "hardware"))]
        cpu = f"{names[0] if names else platform.processor() or 'unknown CPU'}, {os.cpu_count()} cores"
        mem = 0
        for l in (Path("/proc/meminfo").read_text().splitlines() if Path("/proc/meminfo").exists() else []):
            if l.startswith("MemTotal:"):
                mem = int(l.split()[1]) * 1024
    return f"{cpu}, {mem / 2**30:.0f} GB RAM, {platform.system()} {platform.release()} {platform.machine()}"


def bash():
    """The bash that runs install-agents.sh. On Windows that's Git Bash: a bare
    `bash` there finds System32's WSL launcher first, which needs a Linux
    distribution installed."""
    if platform.system() != "Windows":
        return "bash"
    found = shutil.which("bash")
    if found and "system32" not in found.lower():
        return found
    git = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
    if git.exists():
        return str(git)
    sys.exit("install-agents.sh needs Git Bash on Windows")


def install(agents):
    groups = []
    if any(a in NPM for a in agents):
        groups.append("npm")
    if any(a in UV + NEW_UV for a in agents):
        groups.append("uv")
    groups += [a for a in agents if a in NATIVE + EXTRA + NEW_NATIVE]
    for g in groups:
        sh([bash(), str(ROOT / "install-agents.sh"), g])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="only the native binaries: " + ", ".join(NATIVE))
    ap.add_argument("--agents", help="comma-separated subset of: " + ", ".join(ALL))
    ap.add_argument("--reps", type=int, default=REPS, help=f"runs per agent (default {REPS})")
    ap.add_argument("--no-install", action="store_true", help="use what's already installed")
    ap.add_argument("--chanto", help="measure this Chanto binary instead of the pinned release")
    a = ap.parse_args()
    agents = a.agents.split(",") if a.agents else NATIVE if a.quick else PUBLISHED
    unknown = [x for x in agents if x not in ALL]
    if unknown:
        sys.exit(f"unknown agents: {', '.join(unknown)} (choose from {', '.join(ALL)})")

    bench_home = Path(os.environ.get("BENCH_HOME", Path.home() / ".local/share/chanto-bench"))
    chanto = Path(a.chanto).resolve() if a.chanto else bench_home / "bin" / ("chanto.exe" if platform.system() == "Windows" else "chanto")
    # Read by run.py, cputurn.py and size.py when they're imported below.
    os.environ["BENCH_CHANTO_BIN"] = str(chanto)
    if not a.no_install:
        install([x for x in agents if not (x == "chanto" and a.chanto)])
    import cputurn, size
    run = cputurn.run

    def installed(agent):
        if agent == "chanto":
            return chanto.exists()
        if agent == "cline":  # its launcher isn't in node_modules/.bin
            return run.CLINE_BIN.is_file()
        return Path(run.agent_exe(agent)).is_file()

    missing = [x for x in agents if not installed(x)]
    for x in missing:
        print(f"skipping {x}: not installed here (no build for this platform?)", file=sys.stderr)
    agents = [x for x in agents if x not in missing]

    work = Path(tempfile.mkdtemp(prefix="reproduce-"))
    (work / "work").mkdir()
    run.WORK = work / "work"
    run.API_KEY = "x"
    est = len(agents) * a.reps * 8
    print(f"\nMeasuring {len(agents)} agents, {a.reps} runs each, {TURNS} turns reading {BLOB_KB} KB files "
          f"(roughly {est // 60 + 1} min)\n", flush=True)
    raw, starts = {}, {}
    for agent in agents:
        runs, first = [], []
        for i in range(a.reps):
            r = cputurn.one_run(agent, work, TURNS, BLOB_KB)
            if r and r.get("cpu_time") is not None:
                runs.append(r)
            # No turns: one model request, answered with text, then the agent exits.
            r = cputurn.one_run(agent, work, 0, BLOB_KB)
            if r and r.get("cpu_total") is not None:
                first.append(r["cpu_total"])
            print(f"\r  {agent:10} {i + 1}/{a.reps}", end="", flush=True)
        raw[agent], starts[agent] = runs, first
        print(f"\r  {agent:10} done{' ' * 8}", flush=True)
        if not runs:
            # Show why, or a "did not run" row is all anyone gets to go on.
            err = work / f"{agent}.stderr"
            tail = err.read_text(errors="replace").strip().splitlines()[-20:] if err.exists() else []
            print(f"  {agent} made no measurable run; the last lines of its stderr:", file=sys.stderr)
            for l in tail or ["(empty)"]:
                print(f"    {l}", file=sys.stderr)
    shutil.rmtree(work, ignore_errors=True)

    lock_file = size.NPM_ROOT / "package-lock.json"
    lock = json.loads(lock_file.read_text())["packages"] if lock_file.exists() else {}
    rows = []
    for agent in agents:
        runs = raw[agent]
        if not runs:
            rows.append((agent, None, None, None, None, None, None, 0))
            continue
        blended = statistics.median(r["cpu_time"] for r in runs)
        start = statistics.median(starts[agent]) if starts[agent] else None
        # Each full run's CPU without the startup, over the requests after the first.
        turn = [(r["cpu_total"] - start) / (r["turns"] - 1) for r in runs] if start is not None else []
        cpu = statistics.median(turn) if turn else None
        sd = statistics.stdev(turn) if len(turn) > 1 else 0.0
        rss = statistics.median(r["rss"] for r in runs if r.get("rss"))
        try:
            mb = size.measure(agent, lock)[0] / 1e6
        except Exception:
            mb = None
        rows.append((agent, start, cpu, sd, blended, rss, mb, statistics.median(r["turns"] for r in runs)))
    # By per-turn CPU; an agent with no startup run sorts by its whole-run figure.
    rows.sort(key=lambda r: (r[4] is None, r[2] if r[2] is not None else r[4] or 0))
    base = next((r for r in rows if r[0] == "chanto" and r[2]), None)

    name = lambda x: size.AGENTS[x][0]
    out = [f"{'agent':14}{'startup ms':>11}{'ms/turn':>9}{'±sd':>6}{'whole run':>11}{'peak MB':>9}{'install MB':>12}"
           f"  {'× Chanto CPU':>12}{'× mem':>7}  needs",
           "-" * 103]
    for agent, start, cpu, sd, blended, rss, mb, turns in rows:
        if blended is None:
            out.append(f"{name(agent):14}{'did not run':>11}")
            continue
        ratio = f"{cpu / base[2]:.1f}×" if base and cpu is not None else ""
        mratio = f"{rss / base[5]:.1f}×" if base and rss else ""
        note = size.NEEDS.get(agent, "")
        if turns < TURNS:
            note = (note + f" (stopped after {turns:.0f} turns)").strip()
        if agent == "aider":
            note = (note + " (per message: no tool loop)").strip()
        if start is None:
            note = (note + " (no one-request run: startup not separated)").strip()
        num = lambda v, w, f=".1f": f"{v:{w}{f}}" if v is not None else f"{'—':>{w}}"
        out.append(f"{name(agent):14}{num(start, 11, '.0f')}{num(cpu, 9)}{num(sd if cpu is not None else None, 6)}"
                   f"{blended:11.1f}{rss:9.0f}{(f'{mb:.1f}' if mb else '?'):>12}  {ratio:>12}{mratio:>7}  {note}")
    out += ["",
            f"Startup: CPU of a run that makes one model request and exits (median of {a.reps} runs).",
            f"ms/turn: CPU per model request after the first, startup excluded (median of {a.reps} runs).",
            "Whole run: the full run's CPU over all its requests, startup included (the earlier single figure).",
            "CPU is user+sys time of the agent and everything it started. × Chanto CPU compares ms/turn.",
            "Peak MB: largest resident memory of the agent's whole process tree, sampled every 60 ms.",
            "Install MB: what the pinned install puts on disk; Node and Python, where needed, aren't counted."]
    table = "\n".join(out)
    print("\n" + table)

    versions = {x: (run.first_line([str(chanto), "--version"]) if x == "chanto" else
                    run.first_line(run.VERSION_CMDS[x]) if x in run.VERSION_CMDS else "unknown") for x in agents}
    stamp = time.strftime("%Y%m%d-%H%M%S")
    header = [f"# reproduce.py: agent overhead against a local mock model",
              f"# command: python3 reproduce.py {' '.join(sys.argv[1:])}".rstrip(),
              f"# settings: {TURNS} turns, {BLOB_KB} KB files, {a.reps} reps",
              f"# machine: {machine()}",
              *[f"# {x}: {v}" for x, v in versions.items()],
              f"# date: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}", ""]
    detail = ["", "Every run (whole-run CPU ms total, peak MB, requests):",
              *[f"  {x}: " + ", ".join(f"{r['cpu_total']:.1f}/{r['rss'] or 0:.0f}/{r['turns']}" for r in raw[x]) for x in agents],
              "", "Every one-request run (CPU ms total):",
              *[f"  {x}: " + ", ".join(f"{s:.1f}" for s in starts[x]) for x in agents]]
    path = run.RESULTS / f"overhead-{stamp}.txt"
    path.parent.mkdir(exist_ok=True)
    # UTF-8 everywhere: Windows would otherwise write its own code page.
    path.write_text("\n".join(header) + table + "\n" + "\n".join(detail) + "\n", encoding="utf-8")
    print(f"\nSaved {path.relative_to(ROOT)}. Compare the ratios with RESULTS.md; absolute numbers vary by machine.")


if __name__ == "__main__":
    main()
