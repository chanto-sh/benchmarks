"""Exercise the agent's Makefile in a scratch copy of the workspace (with the
original data/ and test/ restored) and check make's behaviour, not its text."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ws, pristine = Path(sys.argv[1]), Path(sys.argv[2])


def expected(datadir):
    skus = {}
    files = sorted(datadir.glob("*.csv"))
    for p in files:
        for line in p.read_text().splitlines()[1:]:
            sku, qty, price = line.split(",")
            s = skus.setdefault(sku, [0, Decimal("0")])
            s[0] += int(qty)
            s[1] += int(qty) * Decimal(price)
    return {"files": len(files), "skus": {k: {"units": u, "revenue": str(r.quantize(Decimal("0.01")))}
                                          for k, (u, r) in sorted(skus.items())}}


def make(repo, *args):
    r = subprocess.run(["make", *args], cwd=repo, capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout + r.stderr


def fail(msg, out=""):
    print("FAIL:", msg)
    if out:
        print(out[-1500:])
    sys.exit(1)


def age(repo):
    """Push every existing file into the past, so the next write is newer."""
    import time
    old = time.time() - 100
    for p in repo.rglob("*"):
        os.utime(p, (old, old))


with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp) / "repo"
    shutil.copytree(ws, repo, ignore=shutil.ignore_patterns(".git", "dist", "__pycache__"))
    for d in ("data", "test"):
        shutil.rmtree(repo / d, ignore_errors=True)
        shutil.copytree(pristine / d, repo / d)
    summary = repo / "dist" / "summary.json"

    code, out = make(repo, "-n")
    if code:
        fail("make -n fails", out)
    code, out = make(repo)
    if code:
        fail("make (default goal) fails", out)
    if not summary.exists() or json.loads(summary.read_text()) != expected(repo / "data"):
        fail("dist/summary.json wrong after a fresh build", out)
    code, out = make(repo, "-q", "dist/summary.json")
    if code != 0:
        fail("a second `make build` with no changes would redo work (not incremental)", out)

    # Edit an existing export: must rebuild.
    age(repo)
    with open(repo / "data" / "store_north.csv", "a") as f:
        f.write("C300,4,2.25\n")
    code, out = make(repo, "build")
    if code or json.loads(summary.read_text()) != expected(repo / "data"):
        fail("editing a CSV did not rebuild dist/summary.json", out)

    # Add a new export: must rebuild and include it.
    age(repo)
    (repo / "data" / "store_east.csv").write_text("sku,qty,unit_price\nD400,7,1.05\nA100,1,4.50\n")
    code, out = make(repo, "build")
    if code or json.loads(summary.read_text()) != expected(repo / "data"):
        fail("adding a CSV did not rebuild dist/summary.json", out)

    # A bad row: the build must fail, and keep failing on a rerun.
    age(repo)
    (repo / "data" / "store_west.csv").write_text("sku,qty,unit_price\nA100,2,4.50\nB200,two,19.99\n")
    code, out = make(repo, "build")
    if code == 0:
        fail("build with a bad row succeeded", out)
    code, out = make(repo, "build")
    if code == 0:
        fail("rerun after a failed build reported success (stale/truncated summary kept)", out)
    (repo / "data" / "store_west.csv").unlink()
    code, out = make(repo, "build")
    if code or json.loads(summary.read_text()) != expected(repo / "data"):
        fail("build did not recover after removing the bad file", out)

    # make test runs the suite, and fails when a test fails.
    code, out = make(repo, "test")
    if code or "Ran 1 test" not in out:
        fail("make test did not run the tests", out)
    (repo / "test" / "test_zz_hidden.py").write_text(
        "import unittest\n\nclass T(unittest.TestCase):\n    def test_fails(self):\n        self.fail('hidden')\n")
    code, out = make(repo, "test")
    if code == 0:
        fail("make test passed with a failing test (tests are not really run)", out)
    (repo / "test" / "test_zz_hidden.py").unlink()

    code, out = make(repo, "clean")
    if code or (repo / "dist").exists():
        fail("make clean did not remove dist/", out)
    if not (repo / "data" / "store_north.csv").exists() or not (repo / "scripts" / "summarize.py").exists():
        fail("make clean removed sources")
print("makefile ok")
