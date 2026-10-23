import subprocess, sys, unittest


def run(*a):
    return subprocess.run([sys.executable, "-m", "todo", *a], capture_output=True, text=True)


class Limit(unittest.TestCase):
    def test_limit(self):
        r = run("list", "--limit", "2")
        self.assertEqual((r.returncode, r.stdout.splitlines()), (0, ["1. write report", "2. buy milk"]))
        self.assertEqual(len(run("list", "--limit", "9").stdout.splitlines()), 5)

    def test_bad_values(self):
        for bad in ("0", "-1", "abc"):
            r = run("list", "--limit", bad)
            self.assertEqual(r.returncode, 2, f"AGENTS.md: bad input exits 2 ({bad})")
            lines = r.stderr.strip().splitlines()
            self.assertEqual(len(lines), 1, f"one stderr line ({bad}): {r.stderr!r}")
            self.assertTrue(lines[0].startswith("error: "), f"AGENTS.md: stderr starts with 'error: ' ({bad}): {r.stderr!r}")
            self.assertEqual(r.stdout, "", f"nothing on stdout ({bad})")


if __name__ == "__main__":
    unittest.main()
