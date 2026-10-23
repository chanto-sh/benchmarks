"""Execute .ci/pipeline.yml like the CI runner: a small YAML subset (maps,
lists of maps, scalars, `|` blocks), every job's steps in order with bash -e.
The pipeline comes from the agent's workspace; everything else comes from the
pristine task files, so only pipeline changes can make it pass."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse(text):
    lines = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        lines.append(raw.rstrip())
    pos = 0

    def indent(l):
        return len(l) - len(l.lstrip(" "))

    def scalar(v):
        v = v.strip()
        if " #" in v and not v.startswith(("'", '"')):
            v = v.split(" #", 1)[0].strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            return v[1:-1]
        return v

    def block(ind):
        nonlocal pos
        if pos >= len(lines):
            return None
        if lines[pos].lstrip().startswith("- "):
            return seq(indent(lines[pos]))
        return mapping(indent(lines[pos]))

    def mapping(ind, first=None):
        nonlocal pos
        out = {}
        while pos < len(lines) or first is not None:
            if first is not None:
                content, first = first, None
            else:
                l = lines[pos]
                if indent(l) != ind or l.lstrip().startswith("- "):
                    if indent(l) > ind:
                        raise SystemExit(f"pipeline: unexpected indentation: {l!r}")
                    break
                content = l.strip()
                pos += 1
            m = re.match(r"^([A-Za-z0-9_.\-]+):(?:\s+(.*))?$", content)
            if not m:
                raise SystemExit(f"pipeline: cannot parse {content!r}")
            k, v = m.group(1), m.group(2)
            if v is None or v == "":
                out[k] = block(ind) if pos < len(lines) and indent(lines[pos]) > ind else None
            elif v.strip() in ("|", "|-"):
                buf = []
                bind = None
                while pos < len(lines) and indent(lines[pos]) > ind:
                    bind = bind if bind is not None else indent(lines[pos])
                    buf.append(lines[pos][bind:])
                    pos += 1
                out[k] = "\n".join(buf) + "\n"
            else:
                out[k] = scalar(v)
        return out

    def seq(ind):
        nonlocal pos
        out = []
        while pos < len(lines) and indent(lines[pos]) == ind and lines[pos].lstrip().startswith("- "):
            content = lines[pos].strip()[2:].strip()
            pos += 1
            if re.match(r"^[A-Za-z0-9_.\-]+:", content):
                out.append(mapping(ind + 2, first=content))
            else:
                out.append(scalar(content))
        return out

    doc = mapping(0)
    if pos != len(lines):
        raise SystemExit(f"pipeline: trailing content at {lines[pos]!r}")
    return doc


def main(pipeline, pristine):
    doc = parse(Path(pipeline).read_text())
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        shutil.copytree(pristine, repo)
        shutil.copy(pipeline, repo / ".ci" / "pipeline.yml")
        base = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "TMPDIR")}
        base.update({k: str(v) for k, v in (doc.get("env") or {}).items()})
        ran = []
        for jname, job in (doc.get("jobs") or {}).items():
            jenv = dict(base, **{k: str(v) for k, v in (job.get("env") or {}).items()})
            for step in job.get("steps") or []:
                env = dict(jenv, **{k: str(v) for k, v in (step.get("env") or {}).items()})
                cwd = repo / step.get("working-directory", ".")
                print(f"== {jname} / {step.get('name')}", flush=True)
                if not cwd.is_dir():
                    print(f"working-directory {step.get('working-directory')} does not exist")
                    return 1, ran
                r = subprocess.run(["bash", "-e", "-c", step["run"]], cwd=cwd, env=env,
                                   capture_output=True, text=True, timeout=60)
                sys.stdout.write(r.stdout[-1500:] + r.stderr[-1500:])
                ran.append((step["run"].strip(), r.returncode, r.stdout + r.stderr))
                if r.returncode:
                    print(f"step failed with exit {r.returncode}")
                    return 1, ran
    return 0, ran


if __name__ == "__main__":
    code, ran = main(sys.argv[1], sys.argv[2])
    if code:
        sys.exit(1)
    cmds = [c for c, _, _ in ran]
    required = ["python3 tools/lint.py service/app",
                "python3 tools/gen_build_info.py service/app/_build_info.py",
                "python3 -m unittest discover -s tests -v"]
    for req in required:
        if req not in cmds:
            print(f"required step missing or altered: {req}")
            sys.exit(1)
    test_out = next(o for c, _, o in ran if c == required[2])
    if not re.search(r"Ran 3 tests", test_out) or "OK" not in test_out:
        print("unit tests did not run all 3 tests successfully")
        sys.exit(1)
    print("pipeline ok")
