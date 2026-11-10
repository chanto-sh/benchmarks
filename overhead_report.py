#!/usr/bin/env python3
"""Publish the overhead numbers: the RESULTS.md section, the README copy and
overhead-latest.json, written from reproduce.py's results files.

    # Gather a workflow run's results: copy each OS's results file into
    # results/ and record where it came from.
    python3 overhead_report.py collect --artifacts DIR --jobs jobs.jsonl \\
        --run-id N --out manifest.json

    # Rewrite the overhead section of RESULTS.md and README.md, and
    # overhead-latest.json, from those files.
    python3 overhead_report.py render manifest.json [--pr N] [--summary out.json]

    # For the auto-overhead workflow: which runners to measure again, and the
    # pull request's description.
    python3 overhead_report.py retry --artifacts DIR --jobs jobs.jsonl
    python3 overhead_report.py body summary.json --version X.Y.Z --run-url URL

A manifest lists, for each OS, the results files behind its column: the first
is the run that measured the OS, and any later one stands in for the agents it
measured (as reruns of single agents did on October 31). Each file also names
the workflow run and job it came from, which the section links to. The section's
notes ("What isn't quite like for like" to the end of the section) are written
by hand and carried over unchanged; everything above them is generated.

overhead-latest.json has the same numbers for programs to read. Its first
fields (chanto_version, date, run_url, and each platform's runner, startup_ms,
cpu_ms_per_turn, peak_mb, results and job_url, all Chanto's) keep their place
and meaning; format 2 adds the rest of the table after them:

    format        2
    repo_url, command, model, sorted_by
    settings      {turns, file_kb, reps}
    agents        [{id, name, runtime, version}], in the table's order
    platforms.<OS> (null when the OS has no results, or no Chanto row):
      install_mb  Chanto's install size
      run_url     the run that measured the OS
      machine     {cpu, cores, memory_gb, os, arch, description}
      agents      [{id, name, runtime, startup_ms, cpu_ms_per_turn, peak_mb,
                   install_mb, results, job_url}], in the table's order; an
                  agent that made no measurable run there has null numbers
                  and no results or job_url
"""
import argparse, json, re, shutil, sys
from datetime import datetime
from pathlib import Path

import reproduce, size

ROOT = Path(__file__).resolve().parent
REPO_URL = "https://github.com/chanto-sh/benchmarks"
# Runner label, the OS's name in the table; the order of the table's columns.
RUNNERS = {"macos-latest": "macOS", "ubuntu-latest": "Linux", "windows-latest": "Windows"}
SORT_BY = ["Linux", "macOS", "Windows"]  # the first OS with numbers orders the rows
NOTES = "What isn't quite like for like:"
DASH = "—"
# Where the versions line names an agent differently from the table.
VERSION_NAMES = {"openhands": "OpenHands CLI"}
NAMES = {v[0]: k for k, v in size.AGENTS.items()}


class ReportError(Exception):
    pass


def parse_results(text):
    """A reproduce.py results file: its header and each agent's medians."""
    lines = text.splitlines()
    header = {}
    for line in lines:
        if not line.startswith("# "):
            break
        k, _, v = line[2:].partition(": ")
        header[k] = v
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("-----")) + 1
    except StopIteration:
        raise ReportError("no table in the results file")
    rows = {}
    for line in lines[start:]:
        if not line.strip():
            break
        # Names longer than the column run into the number ("mini-swe-agentdid not run").
        name = next((n for n in sorted(NAMES, key=len, reverse=True) if line.startswith(n)), None)
        if name is None:
            raise ReportError(f"unknown agent in row: {line!r}")
        rest = line[len(name):].split()
        if " ".join(rest[:3]) == "did not run":
            rows[NAMES[name]] = None
            continue
        num = lambda s: None if s in (DASH, "?") else float(s)
        rows[NAMES[name]] = {"startup": num(rest[0]), "cpu": num(rest[1]), "rss": num(rest[4]),
                             "install": num(rest[5])}
    m = re.fullmatch(r"(\d+) turns, (\d+) KB files, (\d+) reps", header.get("settings", ""))
    if not m or "machine" not in header or "date" not in header:
        raise ReportError("results file is missing its settings, machine or date")
    versions = {}
    for key in size.AGENTS:
        v = header.get(key)
        found = re.search(r"\d+\.\d+(?:\.\d+)*", v) if v and not v.startswith(("unavailable", "unknown")) else None
        if v is not None:
            versions[key] = found.group(0) if found else None
    return {"header": header, "rows": rows, "versions": versions,
            "settings": tuple(int(x) for x in m.groups()),
            "date": datetime.strptime(header["date"], "%Y-%m-%dT%H:%M:%SZ")}


def cpu_name(machine):
    m = re.fullmatch(r"(?P<cpu>.*), (?P<cores>\d+) cores, (?P<mem>\d+) GB RAM, (?P<sys>\S+) (?P<rel>\S+) (?P<arch>\S+)",
                     machine)
    if not m:
        raise ReportError(f"can't read the machine line: {machine!r}")
    cpu = shouted = m["cpu"]
    if m["sys"] == "Darwin":
        cpu = re.sub(r"\s*\([^()]*\)$", "", cpu)  # reproduce.py adds the Mac model: "(VirtualMac2,1)"
    cpu = re.sub(r"\((R|TM)\)|\s+\d+-Core Processor|\s+Processor|\s+CPU\b.*", "", cpu, flags=re.I).strip()
    if not re.search("[a-z]", shouted):  # "INTEL(R) XEON(R) PLATINUM 8573C", not "AMD EPYC 7763 64-Core Processor"
        cpu = " ".join(w.capitalize() if w.isalpha() else w for w in cpu.split())
    return cpu, m


def os_name(m):
    sys_, rel = m["sys"], m["rel"]
    if sys_ == "Darwin":
        return f"macOS (Darwin {rel})"
    if sys_ == "Linux":
        k = re.match(r"(\d+\.\d+)(?:\S*-([a-z]+))?$", rel)
        if k:
            return f"Linux {k[1]}" + (f" ({k[2].capitalize()})" if k[2] else "")
        return f"Linux {rel}"
    if sys_ == "Windows":
        w = re.fullmatch(r"(\d+)Server", rel)
        return f"Windows Server {w[1]}" if w else f"Windows {rel}"
    return f"{sys_} {rel}"


def machine(p):
    """A measured platform's runner: the CPU (the words its files' CPUs share),
    cores, memory, OS and architecture, from its first file."""
    cpus = [cpu_name(f["header"]["machine"])[0] for f in p["files"]]
    _, m = cpu_name(p["files"][0]["header"]["machine"])
    out = {"cpu": common_words(cpus), "cores": int(m["cores"]), "memory_gb": int(m["mem"]), "os": os_name(m),
           "arch": m["arch"]}
    out["description"] = f"{out['cpu']}, {out['cores']} cores, {out['memory_gb']} GB RAM, {out['os']}, {out['arch']}"
    return out


def common_words(names):
    words = [n.split() for n in names]
    out = []
    for group in zip(*words):
        if len(set(group)) > 1:
            break
        out.append(group[0])
    return " ".join(out) or names[0]


def link(text, url):
    return f"[{text}]({url})"


def join_and(items, oxford=False):
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + ("," if oxford and len(items) > 2 else "") + " and " + items[-1]


def anchor(heading):
    """GitHub's anchor for a markdown heading."""
    s = re.sub(r"[^\w\- ]", "", heading.lower())
    return s.replace(" ", "-")


def load(manifest, root):
    """Each OS's results, merged across its files: the agents' numbers, and
    which file each agent's numbers came from."""
    repo = manifest.get("repo_url", REPO_URL)
    run_url = lambda run_id: f"{repo}/actions/runs/{run_id}"
    platforms = []
    for p in manifest["platforms"]:
        files = []
        for f in p.get("files", []):
            res = parse_results((root / f["path"]).read_text(encoding="utf-8"))
            res.update(path=f["path"], run_id=f["run_id"], job_id=f.get("job_id"))
            res["url"] = run_url(f["run_id"])
            res["job_url"] = res["url"] + (f"#summary-{f['job_id']}" if f.get("job_id") else "")
            files.append(res)
        rows, source = {}, {}
        for i, res in enumerate(files):
            for agent, row in res["rows"].items():
                if row is not None or agent not in rows:
                    rows[agent] = row
                    if row is not None:
                        source[agent] = i
        platforms.append({"os": p["os"], "runner": p["runner"], "files": files, "rows": rows, "source": source})
    return platforms, run_url


def build(manifest, old_section, root=ROOT):
    """The new section and README body, overhead-latest.json's data, and what
    the run is missing."""
    platforms, run_url = load(manifest, root)
    main_run = manifest["run_id"]
    measured = [p for p in platforms if p["files"]]
    if not measured:
        raise ReportError("no platform has results")
    all_files = [f for p in measured for f in p["files"]]
    settings = {f["settings"] for f in all_files}
    if len(settings) != 1:
        raise ReportError(f"results files use different settings: {sorted(settings)}")
    turns, kb, reps = settings.pop()
    commands = {f["header"].get("command") for p in measured for f in p["files"][:1]}
    if len(commands) != 1:
        raise ReportError(f"platforms ran different commands: {sorted(map(str, commands))}")
    command = commands.pop()
    when = max(f["date"] for p in measured for f in p["files"][:1])

    # Published agents measured on at least one platform.
    agents = [a for a in reproduce.PUBLISHED if any(p["rows"].get(a) for p in measured)]
    versions = {}
    for a in agents:
        seen = {f["versions"].get(a) for f in all_files} - {None}
        if len(seen) > 1:
            raise ReportError(f"{a} has different versions across the results: {sorted(seen)}")
        versions[a] = seen.pop() if seen else None
    name = lambda a: size.AGENTS[a][0]

    # The run's description and its runners.
    n = len(agents)
    pr = manifest.get("pr")
    from_pr = f", from {link(f'#{pr}', manifest.get('repo_url', REPO_URL) + f'/pull/{pr}')}" if pr else ""
    out = [f"Measured {when:%B} {when.day}, {when.year} by the {link(f'reproduce workflow, run {main_run}', run_url(main_run))}\n"
           f"on GitHub's own runners{from_pr}: `{command}`, the {n}\n"
           f"coding agents with at least 5,000 GitHub stars, each run {reps} times; the table\n"
           f"shows medians. Each number is in the summary of that run, under its OS.", ""]
    for p in platforms:
        if not p["files"]:
            out.append(f"- **{p['os']}**: `{p['runner']}`, not measured in this run")
            continue
        first = p["files"][0]
        line = f"- **{p['os']}**: `{p['runner']}`, {machine(p)['description']}"
        if first["run_id"] != main_run:
            line += ", measured separately in " + link(f"run {first['run_id']}", first["url"])
        extras = []
        for i, f in enumerate(p["files"][1:], 1):
            who = [name(a) for a in agents if p["source"].get(a) == i]
            if who and f["run_id"] != first["run_id"]:
                extras.append(join_and(who) + " from " + link(f"run {f['run_id']}", f["url"]))
        if extras:
            line += ", with " + join_and(extras)
        out.append(line)

    # The last table's order, so a new run's diff shows only what changed;
    # agents it didn't have go after, alphabetically.
    vname = lambda a: VERSION_NAMES.get(a, name(a))
    by_vname = {vname(a): a for a in agents}
    prev = re.search(r"^Versions: (.*?)\. The model", old_section, re.M)
    ordered = ["chanto"]
    for item in prev[1].split("; ") if prev else []:
        a = by_vname.get(next((v for v in sorted(by_vname, key=len, reverse=True) if item.startswith(v + " ")), None))
        if a and a not in ordered:
            ordered.append(a)
    ordered += sorted((a for a in agents if a not in ordered), key=lambda a: vname(a).casefold())
    out += ["", "Versions: " + "; ".join(f"{vname(a)} {versions[a] or '(not recorded)'}" for a in ordered if a in agents)
            + ". The model is a local mock (`stressmock.py`), not a real one.", ""]

    # The table.
    heads = [link(p["os"], p["files"][0]["job_url"]) if p["files"] else p["os"] for p in platforms]
    out.append(f"| agent | runtime | startup ms, {' | '.join(heads)} | CPU ms/turn, {' | '.join(heads)} | "
               f"peak MB, {' | '.join(heads)} | install MB, {' / '.join(p['os'] for p in platforms)} |")
    out.append("|---|---|" + "--:|" * (3 * len(platforms) + 1))
    sort_os = next(o for o in SORT_BY if any(p["os"] == o for p in measured))
    sort_p = next(p for p in platforms if p["os"] == sort_os)
    key = lambda a: (sort_p["rows"].get(a) is None or sort_p["rows"][a]["cpu"] is None,
                     (sort_p["rows"].get(a) or {}).get("cpu") or 0, name(a).casefold())

    def cell(p, a, field, fmt):
        row = p["rows"].get(a)
        v = row and row[field]
        return DASH if v is None else format(v, fmt)

    table_order = sorted(agents, key=key)
    for a in table_order:
        cells = [cell(p, a, f, fmt) for f, fmt in (("startup", ".0f"), ("cpu", ".1f"), ("rss", ".0f")) for p in platforms]
        if a == "chanto":
            cells = [c if c == DASH else f"**{c}**" for c in cells]
        install = " / ".join(cell(p, a, "install", ",.0f") for p in platforms)
        nm = f"**{name(a)}**" if a == "chanto" else name(a)
        out.append(f"| {nm} | {size.AGENTS[a][1]} | " + " | ".join(cells) + f" | {install} |")

    # How it's measured, and the files behind it.
    out += ["", f"""An instant mock model answers every request with a tool call that reads the
next {kb} KB file, for {turns} turns, so the context keeps growing. **Startup** is the
CPU of a run that makes one model request and exits. **CPU per turn** is the
rest of a full run's CPU, startup taken out, over the requests after the
first; before this run the table had one figure that mixed the two, so an
agent slow to start looked costly on every turn. CPU is user + sys time of the
agent's whole process tree; peak memory is the largest resident set of that
tree, sampled every 60 ms; install MB is what the pinned install puts on disk
(Node and Python, where needed, aren't counted). Sorted by {sort_os} CPU per turn."""]
    file_link = lambda f: link(f"`{f['path']}`", f["path"])
    parts = []
    for p in measured:
        files = p["files"]
        if len(files) == 1:
            parts.append(f"{file_link(files[0])}\n({p['os']})")
            continue
        extras = [f"{file_link(f)} ({join_and([name(a) for a in agents if p['source'].get(a) == i]) or 'no agents used'})"
                  for i, f in enumerate(files[1:], 1)]
        tail = extras[0] if len(extras) == 1 else ",\n".join(extras[:-1]) + " and\n" + extras[-1]
        parts.append(f"for {p['os']} {file_link(files[0])},\n{tail}")
    raw = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + ", and " + parts[-1]
    out.append(f"Raw files, with every run's numbers: {raw}.")
    body = "\n".join(out)

    heading = f"Overhead: {n} agents, startup and per turn, mock model ({when:%B} {when.day})"
    i = old_section.find(NOTES)
    if i < 0:
        raise ReportError(f"the old section has no {NOTES!r} notes to carry over")
    section = f"## {heading}\n\n{body}\n\n{old_section[i:]}"
    readme = (f"## Overhead: latest results\n\n{body}\n\n"
              f"Notes on what isn't like for like are in [RESULTS.md](RESULTS.md#{anchor(heading)}).\n\n")

    as_int = lambda v: None if v is None else int(v)

    def agent_numbers(p, a):
        row = p["rows"].get(a)
        out = {"id": a, "name": name(a), "runtime": size.AGENTS[a][1]}
        if not row:
            return {**out, "startup_ms": None, "cpu_ms_per_turn": None, "peak_mb": None, "install_mb": None}
        f = p["files"][p["source"][a]]
        return {**out, "startup_ms": as_int(row["startup"]), "cpu_ms_per_turn": row["cpu"],
                "peak_mb": as_int(row["rss"]), "install_mb": row["install"], "results": f["path"],
                "job_url": f["job_url"]}

    def numbers(p):
        row = p["rows"].get("chanto") if p["files"] else None
        if not row:
            return None
        f = p["files"][p["source"]["chanto"]]
        # Chanto's numbers first, where format 1 had them.
        return {"runner": p["runner"], "startup_ms": as_int(row["startup"]), "cpu_ms_per_turn": row["cpu"],
                "peak_mb": as_int(row["rss"]), "results": f["path"], "job_url": f["job_url"],
                "install_mb": row["install"], "run_url": p["files"][0]["url"], "machine": machine(p),
                "agents": [agent_numbers(p, a) for a in table_order]}

    data = {"chanto_version": versions.get("chanto"), "date": f"{when:%Y-%m-%d}", "run_url": run_url(main_run),
            "platforms": {p["os"]: numbers(p) for p in platforms},
            "format": 2, "repo_url": manifest.get("repo_url", REPO_URL), "command": command,
            "model": "local mock (stressmock.py)", "sorted_by": sort_os,
            "settings": {"turns": turns, "file_kb": kb, "reps": reps},
            "agents": [{"id": a, "name": name(a), "runtime": size.AGENTS[a][1], "version": versions[a]}
                       for a in table_order]}
    missing = [p["os"] for p in platforms if not p["files"]]
    # A different CPU than the last table's is worth a hand-written note.
    hardware = {}
    for p in measured:
        was = re.search(rf"^- \*\*{p['os']}\*\*: `[^`]*`, (.*?), \d+ cores", old_section, re.M)
        now = re.search(rf"^- \*\*{p['os']}\*\*: `[^`]*`, (.*?), \d+ cores", body, re.M)
        if was and now and was[1] != now[1]:
            hardware[p["os"]] = {"was": was[1], "now": now[1]}
    not_run = {p["os"]: [name(a) for a in reproduce.PUBLISHED if not p["rows"].get(a)] for p in measured}
    return section, readme, data, {"missing": missing, "did_not_run": {k: v for k, v in not_run.items() if v},
                                   "hardware_changed": hardware, "chanto_version": versions.get("chanto")}


def split_section(text, heading_prefix):
    """(before, section, after) around the first section whose heading starts so."""
    start = text.find(f"\n## {heading_prefix}")
    if start < 0:
        raise ReportError(f"no '## {heading_prefix}' section")
    start += 1
    end = text.find("\n## ", start)
    end = len(text) if end < 0 else end + 1
    return text[:start], text[start:end], text[end:]


def render(manifest, root=ROOT, pr=None):
    if pr is not None:
        manifest = {**manifest, "pr": pr}
    results_md, readme_md = root / "RESULTS.md", root / "README.md"
    before, old, after = split_section(results_md.read_text(encoding="utf-8"), "Overhead: ")
    section, readme, data, summary = build(manifest, old, root)
    r_before, _, r_after = split_section(readme_md.read_text(encoding="utf-8"), "Overhead: latest results")
    results_md.write_text(before + section + after, encoding="utf-8")
    readme_md.write_text(r_before + readme + r_after, encoding="utf-8")
    (root / "overhead-latest.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return summary


def collect(artifacts, jobs, run_id, results_dir, repo_url=REPO_URL):
    """A manifest from one workflow run's artifacts: `overhead-<runner>` from
    the first measuring job, `overhead-retry-<runner>` from its retry. The
    results files are copied into `results_dir`."""
    platforms = []
    for runner, os_ in RUNNERS.items():
        files = []
        for prefix, caller in (("overhead-retry", "retry"), ("overhead", "measure")):
            found = sorted((artifacts / f"{prefix}-{runner}").glob("overhead-*.txt"))
            if not found:
                continue
            job = next((j["id"] for j in jobs if j.get("name") == f"{caller} / overhead ({runner})"), None)
            for f in found:
                parse_results(f.read_text(encoding="utf-8"))  # refuse anything that isn't one
                dest = results_dir / f.name
                if dest.exists() and dest.read_bytes() != f.read_bytes():
                    raise ReportError(f"{dest} already exists with other contents")
                shutil.copyfile(f, dest)
                files.append({"path": f"{results_dir.name}/{f.name}", "run_id": run_id, "job_id": job})
            break
        platforms.append({"os": os_, "runner": runner, "files": files})
    return {"repo_url": repo_url, "run_id": run_id, "platforms": platforms}


def to_retry(artifacts, jobs, prefix="overhead", caller="measure"):
    """Runners whose job left no results file without failing: cancelled
    (say, no runner became available) or never started. A job that failed
    outright would most likely fail again, so it isn't retried."""
    out = []
    for runner in RUNNERS:
        if list((artifacts / f"{prefix}-{runner}").glob("overhead-*.txt")):
            continue
        job = next((j for j in jobs if j.get("name") == f"{caller} / overhead ({runner})"), None)
        if job is None or job.get("conclusion") != "failure":
            out.append(runner)
    return out


def pr_body(summary, version, run_url, workflow_token=False):
    """The pull request's description, from render's summary. `workflow_token` says the pull request was opened
    with the workflow's own token rather than the automation app's, so its checks haven't started."""
    lines = [f"Measures Chanto {version} against every agent in the overhead table.",
             "",
             f"- Measured by [this auto-overhead run]({run_url}).",
             f"- `install-agents.sh` pins Chanto {version} with the checksums from its `SHA256SUMS`, whose SSH "
             "signature verified against Chanto's release key.",
             "- RESULTS.md's overhead section, its README copy and `overhead-latest.json` are generated by "
             "`overhead_report.py` from the results files this run added under `results/`."]
    if summary.get("missing"):
        lines += ["", f"**Draft: no results for {join_and(summary['missing'])}.** Its job didn't finish, even after "
                  "one retry; that column shows dashes. Run the workflow again by hand (it updates this pull "
                  "request) or measure that OS with the reproduce workflow."]
    for os_, who in summary.get("did_not_run", {}).items():
        lines += ["", f"On {os_}, these agents made no measurable run and show dashes: {join_and(who)}. "
                  "The job's log has each one's stderr."]
    for os_, cpu in summary.get("hardware_changed", {}).items():
        lines += ["", f"GitHub gave the {os_} job a different CPU ({cpu['now']}) than the last table's "
                  f"({cpu['was']}); consider a note above the versions line, as the October 31 table had."]
    lines += ["", "Before merging:",
              "- Check that the notes under the table (carried over unchanged) still match these numbers."]
    if workflow_token:
        lines += ["- The automation app's token wasn't available, so this was opened with the workflow's token, "
                  "which doesn't start other workflows: close and reopen this pull request to start the checks."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect", help="copy a run's results files into results/ and write a manifest")
    c.add_argument("--artifacts", type=Path, required=True, help="the run's downloaded artifacts, one folder each")
    c.add_argument("--jobs", type=Path, required=True, help="the run's jobs, one JSON object per line (id, name)")
    c.add_argument("--run-id", type=int, required=True)
    c.add_argument("--repo-url", default=REPO_URL)
    c.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("render", help="rewrite the overhead section, README copy and overhead-latest.json")
    r.add_argument("manifest", type=Path)
    r.add_argument("--pr", type=int, help="the pull request the measured change came from")
    r.add_argument("--summary", type=Path, help="write what's missing (platforms, agents) here as JSON")
    t = sub.add_parser("retry", help="print the runners to measure again, as a JSON list")
    t.add_argument("--artifacts", type=Path, required=True)
    t.add_argument("--jobs", type=Path, required=True)
    b = sub.add_parser("body", help="print the pull request description")
    b.add_argument("summary", type=Path, help="render's --summary file (missing if nothing was measured)")
    b.add_argument("--version", required=True)
    b.add_argument("--run-url", required=True)
    b.add_argument("--workflow-token", action="store_true",
                   help="opened with the workflow's token, which doesn't start the pull request's checks")
    a = ap.parse_args(argv)
    read_jobs = lambda p: [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    try:
        if a.cmd == "retry":
            print(json.dumps(to_retry(a.artifacts, read_jobs(a.jobs))))
            return 0
        if a.cmd == "body":
            summary = json.loads(a.summary.read_text()) if a.summary.exists() else {"missing": list(RUNNERS.values())}
            print(pr_body(summary, a.version, a.run_url, a.workflow_token), end="")
            return 0
        if a.cmd == "collect":
            m = collect(a.artifacts, read_jobs(a.jobs), a.run_id, ROOT / "results", a.repo_url)
            a.out.write_text(json.dumps(m, indent=2) + "\n")
            print(json.dumps(m, indent=2))
        else:
            summary = render(json.loads(a.manifest.read_text()), pr=a.pr)
            if a.summary:
                a.summary.write_text(json.dumps(summary, indent=2) + "\n")
            print(json.dumps(summary, indent=2))
    except ReportError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
