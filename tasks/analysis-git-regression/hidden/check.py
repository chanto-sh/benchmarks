"""Rebuild the repo privately, find the culprit commit and line, grade answers.json."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from build_repo import CULPRIT, build  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp) / "repo"
    shutil.copytree(HERE.parent / "files", d)
    build(d)
    log = subprocess.run(["git", "log", "--format=%H %s"], cwd=d, capture_output=True, text=True, check=True).stdout
    sha = next(l.split()[0] for l in log.splitlines() if l.split(" ", 1)[1] == CULPRIT)
    src = (d / "invoice/totals.py").read_text().splitlines()
    line = next(i for i, l in enumerate(src, 1) if "// 100" in l and "+ 50" not in l)

try:
    got = json.loads(Path("answers.json").read_text())
except Exception as e:
    sys.exit(f"answers.json missing or not JSON: {e}")
bad = []
c = str(got.get("commit", "")).strip().lower()
if len(c) < 7 or not sha.startswith(c):
    bad.append(f"commit: got {got.get('commit')!r}")
loc = str(got.get("location", "")).strip().lstrip("./")
m = re.fullmatch(r"invoice/totals\.py:(\d+)", loc)
if not m or int(m.group(1)) != line:
    bad.append(f"location: got {got.get('location')!r}")
if bad:
    sys.exit("wrong answers:\n" + "\n".join(bad))
print("all answers correct")
