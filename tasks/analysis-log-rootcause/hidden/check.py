"""Grade answers.json against the facts the generator injected."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gen import generate  # noqa: E402

lines, facts = generate()
try:
    got = json.loads(Path("answers.json").read_text())
except Exception as e:
    sys.exit(f"answers.json missing or not JSON: {e}")


def as_int(v):
    try:
        return int(str(v).strip())
    except ValueError:
        return None


bad = []
# Either the watcher line or the "limits reloaded" line names the change.
if as_int(got.get("root_cause_line")) not in (facts["root_line"] - 1, facts["root_line"]):
    bad.append(f"root_cause_line: got {got.get('root_cause_line')!r}")
if str(got.get("first_failed_request", "")).strip() != facts["failed"][0]:
    bad.append(f"first_failed_request: got {got.get('first_failed_request')!r}")
if as_int(got.get("failed_checkouts")) != len(facts["failed"]):
    bad.append(f"failed_checkouts: got {got.get('failed_checkouts')!r}")
if bad:
    sys.exit("wrong answers:\n" + "\n".join(bad))
print("all answers correct")
