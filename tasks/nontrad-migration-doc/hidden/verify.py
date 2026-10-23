"""Check MIGRATION.md against facts from the repository."""
import re
import sys
from pathlib import Path

ws, pristine = Path(sys.argv[1]), Path(sys.argv[2])
CALLERS = {"app/orders/service.py", "app/billing/invoices.py", "app/admin/tools.py"}
SCHEMA = 14
ENV = {"ORDERS_DB_URL", "ORDERS_DB_POOL", "LEGACY_DB_TIMEOUT_S", "BILLING_CURRENCY"}
errors = []

doc_path = ws / "MIGRATION.md"
if not doc_path.exists():
    print("MIGRATION.md missing")
    sys.exit(1)
doc = doc_path.read_text()

sections = {}
cur = None
for line in doc.splitlines():
    m = re.match(r"^##\s+(.*?)\s*#*\s*$", line)
    if m:
        cur = m.group(1).strip().lower()
        sections[cur] = []
    elif cur is not None:
        sections[cur].append(line)
for name in ("call sites", "schema", "environment", "rollback"):
    if name not in sections:
        errors.append(f"missing section: ## {name}")
sec = {k: "\n".join(v) for k, v in sections.items()}


def ticks(text):
    return [t.strip() for t in re.findall(r"`([^`\n]+)`", text)]


if "call sites" in sec:
    files = set()
    for t in ticks(sec["call sites"]):
        t = re.sub(r":\d+(-\d+)?$", "", t).lstrip("./")
        # Only modules under app/ count; naming the module being retired or its
        # replacement (or a test that patches it) is fine.
        if t.endswith(".py") and t.startswith("app/") and t not in ("app/legacy_db.py", "app/db/session.py"):
            files.add(t)
    if files != CALLERS:
        missing, extra = sorted(CALLERS - files), sorted(files - CALLERS)
        errors.append(f"call sites wrong: missing {missing}, not callers {extra}")
if "schema" in sec:
    m = re.search(r"current schema version:\s*\**\s*v?(\d+)", sec["schema"], re.I)
    if not m:
        errors.append("no 'Current schema version: N' line")
    elif int(m.group(1)) != SCHEMA:
        errors.append(f"schema version {m.group(1)} is wrong")
if "environment" in sec:
    names = {t for t in ticks(sec["environment"]) if re.fullmatch(r"[A-Z][A-Z0-9_]+", t)}
    if names != ENV:
        errors.append(f"environment wrong: missing {sorted(ENV - names)}, not read by the app {sorted(names - ENV)}")
if "rollback" in sec:
    body = [l for l in sec["rollback"].splitlines() if l.strip()]
    if sum(len(l) for l in body) < 40:
        errors.append("rollback section is empty or a stub")

# Hallucinated files: every path-looking reference must exist.
for t in ticks(doc):
    t = re.sub(r":\d+(-\d+)?$", "", t)
    if re.fullmatch(r"[\w./-]+\.(py|md|sql|toml|cfg|ini|json)", t) and "/" in t:
        if not (pristine / t.lstrip("./")).exists():
            errors.append(f"references a file that does not exist: {t}")

# It's a plan only: code must be untouched.
for p in pristine.rglob("*"):
    if p.is_file():
        q = ws / p.relative_to(pristine)
        if not q.exists() or q.read_bytes() != p.read_bytes():
            errors.append(f"changed or removed {p.relative_to(pristine)} (plan only, no code changes)")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print("migration plan ok")
