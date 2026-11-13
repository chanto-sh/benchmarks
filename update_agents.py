#!/usr/bin/env python3
"""Move every agent the benchmark measures to its latest release.

    python3 update_agents.py                    # rewrite the pins
    python3 update_agents.py --dry-run          # only say what would change
    python3 update_agents.py --summary out.md   # also write the changes as Markdown

- npm agents: agents/package.json to each package's latest version, then the
  lockfile (`npm install --package-lock-only --ignore-scripts`).
- Python agents: each `name==version` in install-agents.sh's install_uv to
  PyPI's latest release.
- Binary agents: each to its newest GitHub release (the newest stable one, or
  the newest prerelease for a project that only ships those), with every
  file's checksum taken from GitHub's own SHA-256 digest of it. Grok Build
  comes from x.ai's stable channel instead, pinned only when x.ai and its
  Cloud Storage bucket serve the same bytes.

Pins stay exact, so each measurement names what it measured; this only moves
them. An agent whose new release lacks a file the script installs (a renamed
or dropped build) keeps its old pin, and the summary says so. A release in
BLOCKED is never taken. Chanto is left to chanto_pin.py, which checks its
signed SHA256SUMS.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "install-agents.sh"
AGENTS = ROOT / "agents"

# Releases never to install, with why.
BLOCKED = {
    ("litellm", "1.107.0"): "shipped a credential stealer",
}

# Binary agents from GitHub releases: agent -> (repo, tag prefix, file name for
# a `t=<target>` line). Most lines name their file directly (`f=<file>`).
GITHUB = {
    "goose": ("block/goose", "v", None),
    "opencode": ("sst/opencode", "v", None),
    "codewhale": ("codewhale-hq/Codewhale", "v", None),
    "zerostack": ("gi-dellav/zerostack", "v", None),
    "hax": ("OleksandrChekhovskyi/hax", "v", None),
    "jcode": ("1jehuang/jcode", "v", None),
    "reasonix": ("esengine/DeepSeek-Reasonix", "studio-v", None),
    "omp": ("can1357/oh-my-pi", "v", None),
    "interpreter": ("openinterpreter/openinterpreter", "rust-v", "codex-{t}.tar.gz"),
    "fx": ("vercel-labs/fx", "v", None),
}
GROK = ("https://x.ai/cli", "https://storage.googleapis.com/grok-build-public-artifacts/cli")
HEX = r"[0-9a-f]{64}"
UA = {"User-Agent": "benchmark-agent-update"}


class Skip(Exception):
    """This agent keeps its pin, for the reason given."""


def get(url, token=False):
    headers = dict(UA)
    if token and os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
        return r.read()


def sha256_of(url):
    h = hashlib.sha256()
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
        while chunk := r.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def function(text, name):
    """The span of `name() { ... }` in the script."""
    m = re.search(rf"^{re.escape(name)}\(\) \{{\n.*?^\}}\n", text, re.M | re.S)
    if not m:
        raise SystemExit(f"error: {name} not found in {SCRIPT.name}")
    return m.start(), m.end()


# --- npm ------------------------------------------------------------------------


def update_npm(dry):
    path = AGENTS / "package.json"
    pkg = json.loads(path.read_text())
    changes = []
    for name, pinned in pkg["dependencies"].items():
        latest = json.loads(get(f"https://registry.npmjs.org/{name.replace('/', '%2f')}/latest"))["version"]
        if latest != pinned and (name, latest) not in BLOCKED:
            changes.append((name, pinned, latest))
            pkg["dependencies"][name] = latest
    if changes and not dry:
        path.write_text(json.dumps(pkg, indent=2) + "\n")
        subprocess.run(
            ["npm", "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund"],
            cwd=AGENTS, check=True, stdout=subprocess.DEVNULL,
        )
    return changes


# --- Python (uv tools) --------------------------------------------------------------


def pypi_latest(name):
    info = json.loads(get(f"https://pypi.org/pypi/{name}/json"))
    latest = info["info"]["version"]
    if (name, latest) not in BLOCKED:
        return latest
    # The newest release that isn't blocked, yanked or a prerelease.
    ok = [
        v for v, files in info["releases"].items()
        if files and not all(f.get("yanked") for f in files)
        and (name, v) not in BLOCKED and re.fullmatch(r"[0-9]+(\.[0-9]+)*", v)
    ]
    return max(ok, key=lambda v: tuple(int(x) for x in v.split(".")))


def update_uv(text):
    a, b = function(text, "install_uv")
    body = text[a:b]
    changes = []

    def bump(m):
        name, pinned = m.group(1), m.group(2)
        latest = pypi_latest(name)
        if latest != pinned:
            changes.append((name, pinned, latest))
        return f"{name}=={latest}"

    body = re.sub(r"([A-Za-z0-9_.-]+)==([0-9][^\s]*)", bump, body)
    return text[:a] + body + text[b:], changes


# --- binaries from GitHub releases ---------------------------------------------------


def releases(repo):
    return json.loads(get(f"https://api.github.com/repos/{repo}/releases?per_page=40", token=True))


def pick(rels, prefix):
    ours = [r for r in rels if not r["draft"] and r["tag_name"].startswith(prefix)
            and r["tag_name"][len(prefix):][:1].isdigit()]
    stable = [r for r in ours if not r["prerelease"]]
    # The API lists the newest first.
    return (stable or ours or [None])[0]


def update_github(text, agent):
    repo, prefix, target_file = GITHUB[agent]
    a, b = function(text, f"install_{agent}")
    body = text[a:b]
    # opencode's own downloads (opencode.ai) publish no checksum; its GitHub
    # releases carry the same files with GitHub's digests.
    body = re.sub(r"https://opencode\.ai/files/bin/([0-9][^/]*)/",
                  r"https://github.com/sst/opencode/releases/download/v\1/", body)
    m = re.search(rf"/releases/download/{re.escape(prefix)}([0-9][^/\"\s]*)/", body)
    if not m:
        raise Skip("no pinned release URL found")
    pinned = m.group(1)
    rels = releases(repo)
    new = pick(rels, prefix)
    if not new:
        raise Skip(f"no release tagged {prefix}… on {repo}")
    latest = new["tag_name"][len(prefix):]
    old = next((r for r in rels if r["tag_name"] == prefix + pinned), None)
    if latest == pinned:
        return text[:a] + body + text[b:], None
    if old and new["published_at"] < old["published_at"]:
        raise Skip(f"{prefix}{latest} is older than the pinned {prefix}{pinned}")
    digests = {x["name"]: (x.get("digest") or "").removeprefix("sha256:") for x in new["assets"]}
    body = body.replace(pinned, latest)
    missing = []

    def checksum(name, line):
        d = digests.get(name)
        if not d or not re.fullmatch(HEX, d):
            missing.append(name)
            return line
        return re.sub(HEX, d, line, count=1)

    lines = []
    for line in body.split("\n"):
        if re.search(HEX, line):
            if f := re.search(r"\bf=([^;\s]+);", line):
                line = checksum(f.group(1), line)
            elif (t := re.search(r"\bt=([^;\s]+);", line)) and target_file:
                line = checksum(target_file.format(t=t.group(1)), line)
            elif w := re.search(r"win_install \S+ (\S+) " + HEX, line):
                line = checksum(w.group(1).rsplit("/", 1)[-1], line)
            else:
                missing.append(f"(an unrecognised line: {line.strip()[:60]})")
        lines.append(line)
    if missing:
        raise Skip(f"{prefix}{latest} has no {', '.join(missing)}")
    return text[:a] + "\n".join(lines) + text[b:], (agent, pinned, latest)


def update_grok(text):
    a, b = function(text, "install_grok")
    body = text[a:b]
    pinned = re.search(r"grok-([0-9][^-\"/]*)-", body).group(1)
    channels = {get(f"{base}/stable").decode().strip() for base in GROK}
    if len(channels) != 1:
        raise Skip(f"x.ai and its bucket name different stable versions: {sorted(channels)}")
    latest = channels.pop()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", latest):
        raise Skip(f"unexpected stable version {latest!r}")
    if latest == pinned:
        return text, None
    body = body.replace(pinned, latest)
    lines = []
    for line in body.split("\n"):
        if re.search(HEX, line):
            if p := re.search(r"\bp=([^;\s]+);", line):
                name = f"grok-{latest}-{p.group(1)}"
            elif w := re.search(r"win_install \S+ (\S+) " + HEX, line):
                name = w.group(1).rsplit("/", 1)[-1]
            else:
                raise Skip(f"an unrecognised line: {line.strip()[:60]}")
            sums = {sha256_of(f"{base}/{name}") for base in GROK}
            if len(sums) != 1:
                raise Skip(f"x.ai and its bucket serve different bytes for {name}")
            line = re.sub(HEX, sums.pop(), line, count=1)
        lines.append(line)
    return text[:a] + "\n".join(lines) + text[b:], ("grok", pinned, latest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--summary", type=Path)
    args = ap.parse_args()

    changes, kept = [], []
    changes += [("npm", *c) for c in update_npm(args.dry_run)]
    text = SCRIPT.read_text()
    text, uv = update_uv(text)
    changes += [("uv", *c) for c in uv]
    for agent in GITHUB:
        try:
            text, c = update_github(text, agent)
            if c:
                changes.append(("bin", *c))
        except Skip as e:
            kept.append((agent, str(e)))
    try:
        text, c = update_grok(text)
        if c:
            changes.append(("bin", *c))
    except Skip as e:
        kept.append(("grok", str(e)))
    if not args.dry_run:
        SCRIPT.write_text(text)

    out = []
    if changes:
        out.append("Agents moved to their latest releases:\n")
        out += [f"- {name}: {old} → {new}" for _, name, old, new in changes]
    else:
        out.append("Every agent is already at its latest release.")
    if kept:
        out.append("\nKept at their pins:\n")
        out += [f"- {name}: {why}" for name, why in kept]
    summary = "\n".join(out) + "\n"
    print(summary, end="")
    if args.summary:
        args.summary.write_text(summary)


if __name__ == "__main__":
    main()
