#!/usr/bin/env python3
"""npm audit of the agents' lockfile, with written exceptions.

    python3 audit.py

Runs `npm audit --package-lock-only` in agents/ and fails on any advisory, at
any severity, except those in EXCEPTIONS. An exception names one advisory and
the version of the agent that pulls it in, with why it can't matter here: a
new version of that agent re-checks it, and so does a new advisory.
"""
import json
import subprocess
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parent / "agents"

# (advisory URL, agent package, its pinned version): why it doesn't apply.
EXCEPTIONS = {
    ("https://github.com/advisories/GHSA-g3hv-75wg-m249", "@earendil-works/pi-coding-agent", "1.1.0"):
        "minimatch < 11.0.1 can be slowed by crafted glob patterns. Pi 1.1.0 pins "
        "minimatch 10 and no fixed 10.x exists; forcing 11 would change the agent "
        "being measured. The benchmark only runs Pi against a local mock with fixed "
        "prompts, so no untrusted pattern reaches it.",
}


def main():
    out = subprocess.run(["npm", "audit", "--package-lock-only", "--json"], cwd=AGENTS,
                         capture_output=True, text=True)
    report = json.loads(out.stdout or "{}")
    if "vulnerabilities" not in report:
        sys.exit(f"npm audit gave no report: {out.stderr.strip()}")
    pinned = json.loads((AGENTS / "package.json").read_text()).get("dependencies", {})
    excepted = {(url, agent) for (url, agent, version) in EXCEPTIONS if pinned.get(agent) == version}
    problems = []
    for name, vuln in report["vulnerabilities"].items():
        for via in vuln["via"]:
            if not isinstance(via, dict):
                continue  # A package that is only vulnerable through another one.
            agents = [e for e in vuln.get("effects", [])] or [name]
            # Allowed only when every agent pulling it in has an exception for it.
            if all((via.get("url"), agent) in excepted for agent in agents):
                continue
            problems.append(f"{name} ({via.get('severity')}): {via.get('title')} {via.get('url')}, via {', '.join(agents)}")
    for line in problems:
        print(line)
    if problems:
        sys.exit(f"{len(problems)} advisory(ies) without an exception; see audit.py")
    print(f"npm audit: clean apart from {len(excepted)} written exception(s)")


if __name__ == "__main__":
    main()
