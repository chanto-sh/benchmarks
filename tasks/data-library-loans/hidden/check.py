"""Compare the agent's answers.json with answers recomputed from the pristine data."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from solve import solve  # noqa: E402

TOL = 0.006  # answers are rounded to 2 decimals


def norm(v):
    if isinstance(v, str):
        s = v.strip().rstrip(".").strip().lower()
        try:
            return float(s.replace(",", "")) if s and s[0] in "-0123456789" else s
        except ValueError:
            return s
    if isinstance(v, bool) or v is None:
        return v
    if isinstance(v, (int, float)):
        return float(v)
    return v


def flat(d, pre=""):
    out = {}
    for k, v in (d.items() if isinstance(d, dict) else []):
        key = f"{pre}{str(k).strip().lower()}"
        if isinstance(v, dict):
            out.update(flat(v, key + "."))
        else:
            out[key] = v
    return out


def main():
    expected = solve(Path(__file__).parent.parent / "files")
    try:
        got = json.loads(Path("answers.json").read_text())
    except Exception as e:
        sys.exit(f"answers.json missing or not JSON: {e}")
    expected, got = flat(expected), flat(got)
    bad = []
    for k, want in expected.items():
        g, w = norm(got.get(k)), norm(want)
        if isinstance(w, float):
            ok = isinstance(g, float) and abs(g - w) <= TOL
        else:
            ok = g == w
        if not ok:
            bad.append(f"{k}: got {got.get(k)!r}")
    if bad:
        sys.exit("wrong answers:\n" + "\n".join(bad))
    print("all answers correct")


main()
