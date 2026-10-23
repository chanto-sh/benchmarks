"""The refactor really happened: one shared module, no private copies."""
import ast
import sys
from pathlib import Path

NAMES = {"load_rows", "parse_ts", "in_range", "fmt_money"}
common = Path("reports/common.py")
if not common.exists():
    sys.exit("reports/common.py is missing")
defs = {n.name for n in ast.walk(ast.parse(common.read_text())) if isinstance(n, ast.FunctionDef)}
if not NAMES <= defs:
    sys.exit(f"reports/common.py lacks {sorted(NAMES - defs)}")
for mod in ("csv_export", "json_export", "md_export"):
    tree = ast.parse(Path(f"reports/{mod}.py").read_text())
    fns = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.Lambda)) and hasattr(n, "name")]
    dup = [f for f in fns if f.lstrip("_") in NAMES]
    if dup:
        sys.exit(f"reports/{mod}.py still defines {dup}")
    uses_common = any(
        (isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[-1] == "common")
        or (isinstance(n, ast.ImportFrom) and any(a.name == "common" for a in n.names))
        or (isinstance(n, ast.Import) and any(a.name.endswith("common") for a in n.names))
        for n in ast.walk(tree))
    if not uses_common:
        sys.exit(f"reports/{mod}.py does not import reports.common")
    if "def export" not in Path(f"reports/{mod}.py").read_text():
        sys.exit(f"reports/{mod}.py lost export()")
print("structure ok")
