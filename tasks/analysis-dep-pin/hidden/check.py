"""Grade answers.json for the yaml-lite pin investigation."""
import json
import sys
from pathlib import Path

EXPECTED = {
    "resolved_version": "1.4.2",
    "declared_by": "config-kit@2.4.1",
    "blocking_constraint": ">=1.2.0 <1.5.0",
    "pulled_in_by": "packages/settings/manifest.json:7",
    "config_kit_3_resolves": False,
    "conflict_package": "envparse",
}

try:
    got = json.loads(Path("answers.json").read_text())
except Exception as e:
    sys.exit(f"answers.json missing or not JSON: {e}")


def norm(v):
    if isinstance(v, bool):
        return v
    s = " ".join(str(v).split()).strip().lstrip("./")
    if s.lower() in ("false", "no"):
        return False
    if s.lower() in ("true", "yes"):
        return True
    return s


bad = [f"{k}: got {got.get(k)!r}" for k, want in EXPECTED.items() if norm(got.get(k, "")) != want]
pristine = Path(__file__).parent.parent / "files"
for p in pristine.rglob("*.json"):
    rel = p.relative_to(pristine)
    if not Path(rel).is_file() or Path(rel).read_bytes() != p.read_bytes():
        bad.append(f"{rel} was changed or removed")
if bad:
    sys.exit("wrong answers:\n" + "\n".join(bad))
print("all answers correct")
