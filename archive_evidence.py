#!/usr/bin/env python3
"""Keep the evidence of runs made before run.py saved it itself.

    python3 archive_evidence.py OUT_DIR WORK_DIR...

For each finished run in the work directories (<agent>/<task>-<rep>.out and
its workspace), copies the transcript and the change the agent made. The
grader has already applied the task's hidden tests (test.patch) to these
workspaces, so files that patch touches are left out of the diff; index.json
says so. Runs already archived are skipped, so it can be rerun safely.
"""
import hashlib, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run  # noqa: E402


def patch_files(task):
    p = run.TASKS / task / "test.patch"
    return sorted(set(re.findall(r"^\+\+\+ b/(\S+)", p.read_text(errors="replace"), re.M))) if p.exists() else []


def finished():
    """(agent, task) pairs recorded in the hard tier's result files: a run still
    going has a transcript and workspace too, but they aren't final."""
    done = set()
    for f in sorted(run.RESULTS.glob("2026101*.json")):
        if f.name >= "20261013-232700":  # after the voided first attempt
            try:
                done |= {(r["agent"], r["task"]) for r in json.loads(f.read_text())["results"]}
            except (ValueError, KeyError):
                pass
    return done


def main():
    out, works = Path(sys.argv[1]), [Path(w) for w in sys.argv[2:]]
    done = finished()
    out.mkdir(parents=True, exist_ok=True)
    index_path = out / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    for work in works:
        for transcript in sorted(work.glob("*/*.out")):
            agent = transcript.parent.name
            m = re.match(r"(.+)-(\d+)$", transcript.stem)
            ws = transcript.with_suffix("")
            if not m or not ws.is_dir():
                continue
            task, rep = m[1], int(m[2])
            stem = f"{agent}~{task}~{rep}"
            if stem in index or (agent, task) not in done:
                continue
            excluded = patch_files(task)
            patch = run.workspace_diff(ws, excluded)
            data = transcript.read_bytes()
            (out / f"{stem}.out").write_bytes(data)
            (out / f"{stem}.patch").write_bytes(patch)
            index[stem] = {
                "work_dir": str(work), "transcript_sha256": hashlib.sha256(data).hexdigest(),
                "patch_sha256": hashlib.sha256(patch).hexdigest(),
                "note": "archived after grading; files touched by the hidden tests are excluded from the patch: " + ", ".join(excluded),
            }
            print("archived", stem, flush=True)
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
