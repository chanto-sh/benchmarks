import ast
import sys
from pathlib import Path

bad = []
for p in sorted(Path("shop").rglob("*.py")):
    tree = ast.parse(p.read_text())
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == "query" and p.name == "db.py":
            bad.append(f"{p}: still defines query()")
        if isinstance(n, ast.ImportFrom) and any(a.name == "query" for a in n.names):
            bad.append(f"{p}:{n.lineno}: imports query")
        if isinstance(n, ast.Call):
            f = n.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
            if name == "query":
                bad.append(f"{p}:{n.lineno}: calls query()")
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and "%s" in n.value:
            bad.append(f"{p}:{n.lineno}: legacy %s placeholder")
if bad:
    sys.exit("legacy API still in use:\n" + "\n".join(bad))
print("migration ok")
