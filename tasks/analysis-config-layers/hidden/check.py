"""Grade answers.json: effective production values and the file:line that sets each."""
import json
import sys
from pathlib import Path

EXPECTED = {
    "db.pool_size": ("25", "config/conf.d/9-db-tuning.ini:3"),
    "cache.ttl_seconds": ("120", "deploy/production.env:2"),
    "db.host": ("db.internal", "config/env/production.ini:3"),
    "worker.max_retries": ("5", "config/env/production.ini:9"),
}

try:
    got = json.loads(Path("answers.json").read_text())
except Exception as e:
    sys.exit(f"answers.json missing or not JSON: {e}")
bad = []
pristine = Path(__file__).parent.parent / "files"
for p in pristine.rglob("*"):
    rel = p.relative_to(pristine)
    if p.is_file() and (not Path(rel).is_file() or Path(rel).read_bytes() != p.read_bytes()):
        bad.append(f"{rel} was changed or removed")
for key, (value, source) in EXPECTED.items():
    g = got.get(key) or {}
    gv = str(g.get("value", "")).strip() if isinstance(g, dict) else ""
    gs = str(g.get("source", "")).strip().lstrip("./") if isinstance(g, dict) else ""
    if gv != value or gs != source:
        bad.append(f"{key}: got {g!r}")
if bad:
    sys.exit("wrong answers:\n" + "\n".join(bad))
print("all answers correct")
