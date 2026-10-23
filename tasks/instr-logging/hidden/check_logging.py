import io, os, pathlib, re, tempfile, unittest
from contextlib import redirect_stdout

import cfgload
from cfgload import DEFAULTS, load_config


class Missing(unittest.TestCase):
    def test_defaults_and_warning(self):
        missing = os.path.join(tempfile.mkdtemp(), "nope-7731.json")
        out = io.StringIO()
        with self.assertLogs("cfgload", "WARNING") as logs, redirect_stdout(out):
            got = load_config(missing)
        self.assertEqual(got, DEFAULTS)
        got["theme"] = "x"
        self.assertEqual(DEFAULTS["theme"], "light", "returned the DEFAULTS dict itself")
        self.assertTrue(any("nope-7731.json" in r.getMessage() for r in logs.records), "warning should name the path")
        self.assertEqual(out.getvalue(), "", "AGENTS.md: library code never prints")

    def test_no_print_in_library(self):
        pkg = pathlib.Path(cfgload.__file__).parent
        for f in pkg.glob("*.py"):
            self.assertIsNone(re.search(r"\bprint\(", f.read_text()), f"print() in {f.name}")


if __name__ == "__main__":
    unittest.main()
